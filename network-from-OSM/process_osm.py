import networkx as nx
import osmnx as ox
import time
import numpy as np
from numpy.linalg import norm
from network_elements import*
from collections import defaultdict
from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
from geopy.distance import great_circle

import query_osm as qr
from file_paths import *

SEGMENT_LOWER_BOUND = 20
MERGING_DIST_THRESHOLD = 20
LANE_WIDTH = 3.7 # meters

DEFAULT_LINK_ATTR = {
'width':6,
'lanes':1,
'name':'',
'road_type':1,
'category':1,
'speedlimit': 60,
}

DEFAULT_SEGMENT_ATTR = {
'lanes' : 1,
'capacity' : 1000,
'speedlimit': 60,
'category': 2, #linkCat (metadata)--> A,B,C,D,E
'tag':"",
}

assert DEFAULT_LINK_ATTR['lanes'] == DEFAULT_SEGMENT_ATTR['lanes']

# G = nx.read_gpickle(GRAPH_FILE)
# G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
# G = qr.graph_from_bbox(42.3671,42.3627,-71.1064,-71.0978)
# G = qr.graph_from_bbox(40.1035,39.9009,-74.9870,-75.2503) # Philadelphia
# ox.plot_graph(G)

# print(G.edges(data=True)[0:2])
# print(G.nodes(data=True)[0:2])

def getNodeTypes(G):
    sourceNodes = set()
    sinkNodes = set()
    mergingNodes = set()
    divergingNodes = set()
    intersectionNodes = set()
    trafficLiNodes = set()
    uniNodes = set()

    for node, data in G.nodes(data=True):
        try:
            if data["trafficLid"] != 0:
                trafficLiNodes.append(node)
        except:
            pass
        outEdges = G.out_degree(node)
        inEdges = G.in_degree(node)
        neighbors = set(list(G.predecessors(node)) + list(G.successors(node)))
        num_neighbors = len(neighbors)
        d = G.degree(node)

        if node in neighbors:
            # self-loop
            intersectionNodes.add(node)
        elif inEdges == 0:
            sourceNodes.add(node)
        elif outEdges == 0:
            sinkNodes.add(node)
        elif num_neighbors==2 and (d==2 or d==4):
            uniNodes.add(node)
        elif inEdges == 2 and outEdges == 1:
            mergingNodes.add(node)
        elif inEdges == 1 and outEdges == 2:
            divergingNodes.add(node)
        else:
            intersectionNodes.add(node)
    return {'source':sourceNodes,
            'sink':sinkNodes,
            'uniNodes':uniNodes, # to be removed
            'merging': mergingNodes,
            'diverging': divergingNodes,
            'intersection':intersectionNodes,
            'trafficL':trafficLiNodes}

# Modified OSMnx method. We use our node_type function instead of is_endpoint.
def get_paths_to_simplify(G, uniNodesSet):
    """
    Create a list of all the paths to be simplified between uniNodesSet nodes.

    The path is ordered from the first endpoint, through the interstitial nodes,
    to the second endpoint.

    Parameters
    ----------
    G : networkx multidigraph

    Returns
    -------
    paths_to_simplify : list
    """

    # first identify all the nodes that are endpoints
    start_time = time.time()
    endpoints = set([node for node in G.nodes() if not node in uniNodesSet])
    paths_to_simplify = []

    # for each endpoint node, look at each of its successor nodes
    for node in endpoints:
        for successor in G.successors(node):
            if successor not in endpoints:
                # if the successor is not an endpoint, build a path from the
                # endpoint node to the next endpoint node
                try:
                    path = ox.build_path(G, successor, endpoints, path=[node, successor])
                    paths_to_simplify.append(path)
                except RuntimeError:
                    print("RecursionError")
    return paths_to_simplify

def build_linkGraph(G, uniNodesSet):
    """

    Create a new link graph removing all nodes that are not intersections or
    dead-ends. Each edge (link) will have intersection or dead-end nodes.

    Parameters
    ----------
    G : graph ( will not be modified)

    Returns
    -------
    networkx multidigraph
    """

    linkGraph = G.copy()
    all_nodes_to_remove = []
    all_edges_to_add = []

    # construct a list of all the paths that need to be simplified
    paths = get_paths_to_simplify(G, uniNodesSet)

    start_time = time.time()
    for path in paths:
        edge_attributes = {}
        all_edges = zip(path[:-1], path[1:])
        for u, v in all_edges:
            # each edge:
            # {'osmid': 8614961, 'oneway': True, 'lanes': '1', 'name': 'Pearl Street', 'highway': 'tertiary', 'width': '12.2', 'length': 72.679754393141266}

            # there shouldn't be multiple edges between interstitial nodes
            if not G.number_of_edges(u=u, v=v) == 1:
                # OSM data has multiple edges !!!
                print('Multiple edges between "{}" and "{}" found when merging path ends: '.format(u, v))
            edge = G.edges[u, v, 0]
            for key in edge:
                if key in edge_attributes:
                    edge_attributes[key].append(edge[key])
                else:
                    edge_attributes[key] = [edge[key]]

        # Combine intermediate edge attributes and build segments.
        for key in edge_attributes:
            # print(type(edge_attributes), edge_attributes)
            # don't touch the length attribute, we'll sum it at the end
            if key=='name':
                try:
                    edge_attributes[key] = edge_attributes[key][0].encode('utf-8')
                except:
                    edge_attributes[key] = ""
            # try:
            #     name = data['name'].encode('utf-8')
            # except:
            #     name = DEFAULT_LINK_ATTR['name']
            # try:
            #     lanes = int(data['lanes'])
            # except:
            #     lanes = DEFAULT_LINK_ATTR['lanes']
            elif not key == 'length':
                # keep one of each value in this attribute list,
                # consolidate it to the single value (the zero-th)
                edge_attributes[key] = edge_attributes[key][0]

        edge_attributes['length'] = sum(edge_attributes['length'])
        edge_attributes['coordinates'] = path
        # add the nodes and edges to their lists for processing at the end
        all_nodes_to_remove.extend(path[1:-1])
        all_edges_to_add.append({'origin':path[0],
                                 'destination':path[-1],
                                 'attr_dict':edge_attributes})

    # finally remove all the interstitial nodes between the new edges
    linkGraph.remove_nodes_from(set(all_nodes_to_remove))
    for edge in all_edges_to_add:
        linkGraph.add_edge(edge['origin'], edge['destination'], **edge['attr_dict'])

    # set all attributes, using default values
    for u,v,key,data in linkGraph.edges(keys=True, data=True):
        if not 'coordinates' in data:
            linkGraph.edges[u,v,key]['coordinates'] = [u,v]
        for attr in DEFAULT_LINK_ATTR:
            if attr not in data:
                linkGraph.edges[u,v,key][attr] = DEFAULT_LINK_ATTR[attr]

    msg = '--------------  Link graph (from {:,} to {:,} nodes and from {:,} to {:,} edges) in {:,.2f} seconds'
    # print(msg.format(len(list(G.nodes())), len(list(linkGraph.nodes())), len(list(G.edges())), len(list(linkGraph.edges())), time.time()-start_time))
    return linkGraph

# cut from the start coordinate.
def interCoord(fromPoint, toPoint, lenght, G, fromTailSide=True):
    proportion = lenght/G.edges[fromPoint, toPoint, 0]['length']
    dx = (G.nodes[toPoint]['x'] - G.nodes[fromPoint]['x']) * proportion
    dy = (G.nodes[toPoint]['y'] - G.nodes[fromPoint]['y']) * proportion
    if fromTailSide:
        x,y = G.nodes[fromPoint]['x'] + dx, G.nodes[fromPoint]['y'] + dy
    else:
        x,y = G.nodes[toPoint]['x'] - dx, G.nodes[toPoint]['y'] - dy
    # assert 0.1 > (distanceNodes(fromPoint, toPoint, G) - distance(fromPoint, (y,x), G) - distance(toPoint, (y,x), G))
    return x,y

def coordsLen(coordinates, G):
    totalLen = 0
    geoLen = 0
    for tail, head in zip(coordinates[:-1], coordinates[1:]):
        totalLen += G.edges[tail, head, 0]['length']
        geoLen += distanceNodes(tail, head, G)
    # assert 0.1 > totalLen - geoLen
    return totalLen


def shortenFromTail(ends, G, originalG, size):
    coordinates = G.edges[ends[0], ends[1], ends[2]]['coordinates']
    length = 0
    head = 1 # first node will be definitely get removed.
    while head < len(coordinates):
        next_edge = originalG.edges[coordinates[head-1], coordinates[head], 0]['length']
        if size < length + next_edge:
            break
        length  += next_edge
        head += 1

    if head == len(coordinates):
        msg = 'Cut {:,} is too long for the link between {:,} and {:,} nodes, size of {:,}'
        # print(msg.format(size, ends[0], ends[1], length))
    else:
        # shorten from the TAIL node side
        newx, newy = interCoord(coordinates[head-1], coordinates[head], size-length, originalG, fromTailSide=True)
        originalG.max_node_id += 1
        new_coordinates = [originalG.max_node_id] + coordinates[head:]
        G.edges[ends[0], ends[1], 0]['coordinates'] = new_coordinates

        # add node info to the original graph
        originalG.add_node(originalG.max_node_id, x=newx, y=newy)
        originalG.add_edge(originalG.max_node_id, coordinates[head], length=distanceNodes(originalG.max_node_id, coordinates[head], originalG))

        # Validate
        before_shorten = coordsLen(coordinates, originalG)
        after_shorten = coordsLen(new_coordinates, originalG)
        # assert 0.1 > before_shorten - after_shorten - size


def shortenFromHead(ends, G, originalG, size):
    coordinates = G.edges[ends[0], ends[1], ends[2]]['coordinates']
    length = 0
    tail = len(coordinates) - 2 # first node will be definitely get removed.
    while tail >= 0:
        next_edge = originalG.edges[coordinates[tail], coordinates[tail+1], 0]['length']
        if size < length + next_edge:
            break
        length  += next_edge
        tail -= 1

    if tail < 0:
        msg = 'Cut {:,} is too long for the link between {:,} and {:,} nodes, size of {:,}'
        # print(msg.format(size, ends[0], ends[1], length))
    else:
        # shorten from the HEAD node side
        newx, newy = interCoord(coordinates[tail], coordinates[tail+1], size-length, originalG, fromTailSide=False)
        originalG.max_node_id += 1
        new_coordinates = coordinates[:tail+1] +[originalG.max_node_id]
        G.edges[ends[0], ends[1], 0]['coordinates'] = new_coordinates

        # add node info to the original graph
        originalG.add_node(originalG.max_node_id, x=newx, y=newy)
        originalG.add_edge(coordinates[tail], originalG.max_node_id, length=distanceNodes(originalG.max_node_id, coordinates[tail], originalG))

        # Validate
        before_shorten = coordsLen(coordinates, originalG)
        after_shorten = coordsLen(new_coordinates, originalG)
        # assert 0.1 > before_shorten - after_shorten - size

def distanceNodes(node1, node2, G):
    return great_circle((G.nodes[node1]['y'], G.nodes[node1]['x']), (G.nodes[node2]['y'], G.nodes[node2]['x'])).meters

def distance(node1, coord, G):
    return great_circle((G.nodes[node1]['y'], G.nodes[node1]['x']), (coord[0], coord[1])).meters

def constructNodesLinks(G, originalG, tempnodeDict):
    nodes = {}
    links = {}
    link_id = 1

    for fromnode, tonode, key, data in G.edges(keys=True,data=True):
        # TODO: road_type, category?
        try:
            name = data['name'].encode('utf-8')
        except:
            name = DEFAULT_LINK_ATTR['name']
        try:
            lanes = int(data['lanes'])
        except:
            lanes = DEFAULT_LINK_ATTR['lanes']

        link = Link(link_id,
                    data['road_type'],
                    data['category'],
                    fromnode,
                    tonode,
                    name,
                    lanes,
                    int(data['speedlimit']))
        G.edges[fromnode, tonode, key]['id'] = link_id
        G.edges[fromnode, tonode, key]['name'] = name
        G.edges[fromnode, tonode, key]['lanes'] = lanes
        links[link_id] = link
        link_id += 1

    coordinates = nx.get_edge_attributes(G,'coordinates')
    # for u,v,data in G.edges():

    max_node_id = max(originalG.nodes())
    originalG.max_node_id = max_node_id

    new_nodes = []
    for nodeId, data in G.nodes(data=True):
        nodeType = 0
        trafficLid = 0
        if nodeId in tempnodeDict['intersection']:
            nodeType = 2
        elif nodeId in tempnodeDict['diverging'] or tempnodeDict['merging']:
            nodeType = 3
        elif nodeId in tempnodeDict['source'] or tempnodeDict['sink']:
            nodeType = 1

        try:
            if data["trafficLid"] != 0:
                trafficLiNodes.append(node)
        except:
            pass
        node = Node(nodeId, nodeType, trafficLid, data['x'], data['y'])
        nodes[nodeId] = node

        # turning path radius for intersections
        if nodeId: #in tempnodeDict['uniNodes']:
            in_edges = [((u,v, key), int(data['lanes'])) for u,v,key,data in G.in_edges(nodeId, keys=True, data=True)]
            out_edges = [((u,v, key), int(data['lanes'])) for u,v,key,data in G.out_edges(nodeId, keys=True, data=True)]
            maxRadius = max([ edge[1] * LANE_WIDTH for edge in in_edges + out_edges]) # width * lanes
            for ends, _ in in_edges:
                 new_node = shortenFromHead(ends, G, originalG, maxRadius)
                 new_nodes.append(new_node)
            for ends, _ in out_edges:
                new_node = shortenFromTail(ends, G, originalG, maxRadius)
                new_nodes.append(new_node)
    return nodes, links


def geoFromPathGraph(G, originalG):
    pathGeo = {}
    coords = nx.get_edge_attributes(G,'coordinates')
    for link in coords:
        pathGeo[link] = LineString([Point((originalG.nodes[node]['x'], originalG.nodes[node]['y'])) for node in coords[link]])
    nx.set_edge_attributes(G, 'coordinates', pathGeo)


def attr(data, attr):
    if attr in data:
        if attr == 'width' or attr == 'lanes':
            try:
                return float(data[attr])
            except:
                return DEVAULT_OSM_VALUE[attr]
        return data[attr]
    else:
        return DEVAULT_OSM_VALUE[attr]

def attr2(data, attr):
    if attr in data:
        if attr == 'width' or attr == 'lanes':
            try:
                return float(data[attr])
            except:
                return DEVAULT_OSM_VALUE[attr]
        return data[attr]
    else:
        return DEVAULT_OSM_VALUE[attr]

def attribute(att_string, sub_attribute, parent_attribute, default_attribute):
    if att_string in sub_attribute:
        return sub_attribute[att_string]
    elif att_string in parent_attribute:
        return parent_attribute[att_string]
    return default_attribute[att_string]

def constructSegments(linkGraph, originalG, SEGMENT_LOWER_BOUND=20):
    linkToSeg = {}
    linkToData = {}
    segToLink = {}
    toSegment = {}
    SEGMENT_ID = 1

    for u,v,key,linkData in linkGraph.edges(keys=True,data=True):
        coords = linkData['coordinates']
        link_id = linkData['id']
        linkToData[link_id] = linkData
        linkToSeg[link_id] = []
        total_len = sum([originalG.edges[coords[i], coords[i+1], 0]['length'] for i in range(len(coords)-1)]) # after shortened
        tail = 0
        segment_len = 0
        acc_len = 0
        segment_coords = [coords[tail]]
        segment_attributes = {}
        SEQ = 1
        while tail < len(coords)-1:
            data = originalG.edges[coords[tail], coords[tail+1], 0]
            for key in data:
                segment_attributes[key] = data[key] # get whatever available
            segment_len += data['length']
            acc_len += data['length']
            if total_len - acc_len < SEGMENT_LOWER_BOUND or tail == len(coords)-2:
                # combine all leftover coordinates if they are not enough for a segment.
                segment_coords += coords[tail+1:]
                toSegment[SEGMENT_ID] = (segment_coords, segment_attributes, segment_len, link_id, SEQ)
                linkToSeg[link_id].append(SEGMENT_ID)
                SEGMENT_ID += 1
                SEQ += 1
                # print("case1",segment_len )
                break
            elif segment_len > SEGMENT_LOWER_BOUND:
                # a new segment
                segment_coords.append(coords[tail+1])
                toSegment[SEGMENT_ID] = (segment_coords, segment_attributes, segment_len, link_id, SEQ)
                linkToSeg[link_id].append(SEGMENT_ID)
                segment_coords = [coords[tail+1]]
                segment_attributes = {}
                # print("case2",segment_len )
                segment_len = 0
                SEGMENT_ID += 1
                SEQ += 1
            else:
                # print("case3-coord",segment_len )
                segment_coords.append(coords[tail+1])
            tail += 1

    segments = {}
    for segment_id in toSegment:
        coords, segment_attributes, length, link_id, seq = toSegment[segment_id]
        coords_data = [originalG.nodes[node] for node in coords]
        position_points = [ {'x': data['x'],
                            'y': data['y'],
                            'seq': i} for i, data in enumerate(coords_data)]
        for attr in DEFAULT_SEGMENT_ATTR:
            if attr not in segment_attributes:
                if attr in linkToData[link_id]:
                    segment_attributes[attr] = linkToData[link_id][attr]
                else:
                    segment_attributes[attr] = DEFAULT_SEGMENT_ATTR[attr]

        seg = Segment(
                segment_id,
                link_id,
                seq,
                int(linkToData[link_id]['lanes']), # force to the same number of lanes for segments in the same link
                int(segment_attributes['capacity']),
                int(segment_attributes['speedlimit']),
                segment_attributes['tag'],
                segment_attributes['category'],
                position_points,
                length)
        segToLink[segment_id] = link_id
        segments[segment_id] = seg
    return segments, segToLink, linkToSeg

def setLinkSegmentAttr(segments, links, linkToSeg):
    # Contructing Link Travel Time Table
    linktts = {}
    for link_id in links:
        links[link_id].segments = linkToSeg[link_id]
        linkTime,linkLength = 0,0
        for segid in links[link_id].segments:
            segLength = segments[segid].length
            segTime =  segLength/(segments[segid].speedlimit*(0.277778))
            linkLength += segLength
            linkTime += segTime
        #length = getLength(pointList)
        #traveltime = length/20.833    #75kmph in m/s
        linktts[link_id] = LinkTT(link_id,mode="Car",starttime="00:00:00",endtime="23:59:59",traveltime=linkTime,length=linkLength)
    return linktts


def processAndAddConnections(nodes,tempnodeDict,links,segments,lanes,laneconnections,turninggroups,segToLink):
    '''
    '''
    laneswithDwConn = []  # lanes with downstream connections
    laneswithUpConn = []  # lanes with upstream connections

    for connid,conn in laneconnections.iteritems():
        fLane,tLane = conn.fromlane,conn.tolane
        laneswithDwConn.append(fLane)
        laneswithUpConn.append(tLane)
    laneswithDwConn,laneswithUpConn = set(laneswithDwConn),set(laneswithUpConn)

    totLaneList = lanes.keys()
    terlaneswithoutDwConn, terlaneswithoutUpConn = set(),set()

    #---Getting the terminal lanes ---lanes at the end and begining of links--- that are not connected to sink (source) node and no downstream (upstream) connection
    for linkid,link in links.iteritems():
        tnode,hnode = link.upnode,link.dnnode
        #---first segment
        segid = link.segments[0]
        segment = segments[segid]
        for i in xrange(segment.numlanes):
            laneid = str(int(segid)*100 + i)
            if laneid not in laneswithUpConn and tnode not in tempnodeDict['source']:
                terlaneswithoutUpConn.add(laneid)
        #---last segment
        segid = link.segments[-1]
        segment = segments[segid]
        for i in xrange(segment.numlanes):
            laneid = str(int(segid)*100 + i)
            if laneid not in laneswithDwConn and hnode not in tempnodeDict['sink']:
                terlaneswithoutDwConn.add(laneid)


    #----Handling lanes without downstream connections
    unresolvedLanes = []
    connKeylist = laneconnections.keys()
    count = len(connKeylist) + 1 # count and id of the connections
    #---Copying the connections from one of the adjacent lanes
    for laneid1 in terlaneswithoutDwConn:
        resolved = False
        segid1 = laneid1[:-2]
        segid1 = int(segid1)
        for i in xrange(segments[segid1].numlanes):
            laneid2 = str(int(segid1)*100 + i)
            if laneid1!=laneid2:
                connkeys = [key for key in connKeylist if key[0]==laneid2]
                if connkeys:
                    fromLane,toLane = connkeys[0]
                    tosegid = toLane[:-2]
                    linkid1,toLink = segToLink[segid1],segToLink[tosegid]
                    maxSpeed = min(segments[segid1].speedlimit,segments[tosegid].speedlimit)
                    groupid = turninggroups[(linkid1,toLink)].id
                    connection = LaneConnection(count,laneid1,toLane,segid1,tosegid,isturn=True,maxspeed=maxSpeed,groupid=groupid)
                    #---Constructing the connection polyline
                    firstpoint,secondpoint = lanes[laneid1].position[-1],lanes[toLane].position[0]
                    connection.position = [firstpoint,secondpoint]
                    laneconnections[(laneid1,toLane)] = connection
                    count += 1
                    resolved = True
                    break
        if not resolved:
            unresolvedLanes.append(laneid1)
            # pdb.set_trace()

    print "Before: ",len(terlaneswithoutDwConn)
    print "After: ",len(unresolvedLanes), unresolvedLanes
    return laneconnections


import csv,pdb,os,itertools,copy,math

def constructLanes(segments,typeToWidthFname):
    '''
    '''
    catToWidth = {}
    geo_scale = 0.000008
    with open(typeToWidthFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            catToWidth[int(row['CategoryID'])] = row

    #---Contructing lanes attributes
    lanes = {}
    for segid,segment in segments.iteritems():
        for i in xrange(segment.numlanes):
            laneid = int(segid)*100 + i
            width = catToWidth[segment.category]['LaneWidth']
            lane = Lane(id=laneid,segid=segid,width=width)
            lanes[laneid] = lane

    #---Contructing lane polylines
    for segid,segment in segments.iteritems():
        segPos = segment.position
        segPos = [(float(item['x']),float(item['y'])) for item in segPos]
        width = float(catToWidth[segment.category]['LaneWidth'])*geo_scale
        #---looping over the lanes from the slowest to fastest
        for i in xrange(segment.numlanes):
            laneid = int(segid)*100 + i
            if segment.numlanes==1:
                lanePos = segPos
            elif segment.numlanes==2:
                lanePos = offsetPolyLine(segPos,(-0.5+i)*width)
            elif segment.numlanes==3:
                lanePos = offsetPolyLine(segPos,(-1+i)*width)
            elif segment.numlanes==4:
                lanePos = offsetPolyLine(segPos,(-1.5+i)*width)
            elif segment.numlanes==5:
                lanePos = offsetPolyLine(segPos,(-2.+i)*width)
            elif segment.numlanes==6:
                lanePos = offsetPolyLine(segPos,(-2.5+i)*width)
            elif segment.numlanes==7:
                lanePos = offsetPolyLine(segPos,(-3.+i)*width)
            elif segment.numlanes==8:
                lanePos = offsetPolyLine(segPos,(-3.5+i)*width)
            elif segment.numlanes==9:
                lanePos = offsetPolyLine(segPos,(-4.0+i)*width)
            elif segment.numlanes==10:
                lanePos = offsetPolyLine(segPos,(-4.5+i)*width)
            elif segment.numlanes==11:
                lanePos = offsetPolyLine(segPos,(-5.0+i)*width)
            elif segment.numlanes==12:
                lanePos = offsetPolyLine(segPos,(-5.5+i)*width)
            else:
                print "+++ @constructLanes(): The following case is not defined: numLanes: ", segment.numlanes
                pdb.set_trace()

            lanes[laneid].position = lanePos
    return lanes


def offsetPolyLine(polyLine,offset):
    '''
    '''

    if len(polyLine)==1:
        print "+++ @offsetPolyLine(): polyline has only 1 point"
        pdb.set_trace()

    # if abs(offset)<10**-6:
    #     return polyLine
    lineList = []
    # off-set all the lines (pairs of points)
    for point1,point2 in zip(polyLine,polyLine[1:]):
        dx = point2[0]-point1[0]
        dy = point2[1]-point1[1]
        try:
            n = np.array([-dy,dx])/norm([-dy,dx])
        except:
            pdb.set_trace()
        if not type(norm([-dy,dx])) is np.float64:
            pdb.set_trace()

        offpoint1 = np.array(point1) + offset*n
        offpoint2 = np.array(point2) + offset*n
        lineList.append([offpoint1,offpoint2])

    #print lineList
    offsetPolyLine = []
    #---determing the middle points of two offset line
    if len(polyLine)>2:
        for line1,line2 in zip(lineList,lineList[1:]):
            if line1[1][0]-line1[0][0] != 0 and line2[1][0]-line2[0][0] != 0:
                m1 = (line1[1][1]-line1[0][1])/(line1[1][0]-line1[0][0])
                c1 = line1[1][1] - m1*line1[1][0]
                m2 = (line2[1][1]-line2[0][1])/(line2[1][0]-line2[0][0])
                c2 = line2[1][1] - m2*line2[1][0]
                interx = (c2-c1)/(m1-m2)
                intery = m1*interx + c1
                offsetPolyLine.append(np.array([interx,intery]))

    #---inserting the first and last points
    offsetPolyLine.insert(0,lineList[0][0])
    offsetPolyLine.append(lineList[-1][1])

    #---Should be updated to handle exceptions where inf is at the end points
    for i in xrange(len(offsetPolyLine)):
        point = offsetPolyLine[i]
        if point[0]==np.inf or point[1]==np.inf:
            p1,p2 = offsetPolyLine[i-1],offsetPolyLine[i+1]
            newp = (p1+p2)/2.
            offsetPolyLine[i] = newp

    return offsetPolyLine


def clean_intersections(G, tolerance=15, dead_ends=False):
    """
    Clean-up intersections comprising clusters of nodes by merging them and
    returning their centroids.

    Divided roads are represented by separate centerline edges. The intersection
    of two divided roads thus creates 4 nodes, representing where each edge
    intersects a perpendicular edge. These 4 nodes represent a single
    intersection in the real world. This function cleans them up by buffering
    their points to an arbitrary distance, merging overlapping buffers, and
    taking their centroid. For best results, the tolerance argument should be
    adjusted to approximately match street design standards in the specific
    street network.

    Parameters
    ----------
    G : networkx multidigraph
    tolerance : float
        nodes within this distance (in graph's geometry's units) will be
        dissolved into a single intersection
    dead_ends : bool
        if False, discard dead-end nodes to return only street-intersection
        points

    Returns
    ----------
    G : modified and cleaned networkx multidigraph
    """

    if not dead_ends:
        if 'streets_per_node' in G.graph:
            streets_per_node = G.graph['streets_per_node']
        else:
            streets_per_node = ox.count_streets_per_node(G)

        dead_end_nodes = [node for node, count in streets_per_node.items() if count <= 1]
        # G = G.copy()
        G.remove_nodes_from(dead_end_nodes)
    return G
