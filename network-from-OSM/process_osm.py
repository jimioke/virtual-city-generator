import networkx as nx
import osmnx as ox
import time
from network import*
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
# G = nx.read_gpickle(GRAPH_FILE)
# G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
# G = qr.graph_from_bbox(42.3671,42.3627,-71.1064,-71.0978)
# G = qr.graph_from_bbox(40.1035,39.9009,-74.9870,-75.2503) # Philadelphia
# ox.plot_graph(G)

# print(G.edges(data=True)[0:2])
# print(G.nodes(data=True)[0:2])

def getNodeTypes(G):
    sourceNodes = []
    sinkNodes = []
    mergingNodes = []
    divergingNodes = []
    intersectionNodes = []
    trafficLiNodes = []
    uniNodes = []

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
            intersectionNodes.append(node)
        elif inEdges == 0:
            sourceNodes.append(node)
        elif outEdges == 0:
            sinkNodes.append(node)
        elif num_neighbors==2 and (d==2 or d==4):
            uniNodes.append(node)
        elif inEdges == 2 and outEdges == 1:
            mergingNodes.append(node)
        elif inEdges == 1 and outEdges == 2:
            divergingNodes.append(node)
        else:
            intersectionNodes.append(node)
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
            # don't touch the length attribute, we'll sum it at the end
            if len(set(edge_attributes[key])) == 1 and not key == 'length':
                # if there's only 1 unique value in this attribute list,
                # consolidate it to the single value (the zero-th)
                edge_attributes[key] = edge_attributes[key][0]
            elif not key == 'length':
                # otherwise, if there are multiple values, keep one of each value
                edge_attributes[key] = list(set(edge_attributes[key]))

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
    msg = 'Link graph (from {:,} to {:,} nodes and from {:,} to {:,} edges) in {:,.2f} seconds'
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
    assert 0.1 > totalLen - geoLen
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
        assert 0.1 > before_shorten - after_shorten - size


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
        assert 0.1 > before_shorten - after_shorten - size

def distanceNodes(node1, node2, G):
    return great_circle((G.nodes[node1]['y'], G.nodes[node1]['x']), (G.nodes[node2]['y'], G.nodes[node2]['x'])).meters

def distance(node1, coord, G):
    return great_circle((G.nodes[node1]['y'], G.nodes[node1]['x']), (coord[0], coord[1])).meters

def constructNodesLinks(G, originalG, tempnodeDict):
    nodes = {}
    links = {}
    link_id = 1

    for upnode, dnnode, key, data in G.edges(keys=True,data=True):
        # TODO: road_type, category?
        link = Link(link_id, 1, 1, upnode, dnnode, attr(data, 'name'))
        G.edges[upnode, dnnode, key]['id'] = link_id
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
        # TODO: use a set or get id to type dic (efficiency)
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
            in_edges = [((u,v, key), attr(data, 'lanes')) for u,v,key,data in G.in_edges(nodeId, keys=True, data=True)]
            out_edges = [((u,v, key), attr(data, 'lanes')) for u,v,key,data in G.out_edges(nodeId, keys=True, data=True)]
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

def mergeClusteringIntersection(G):
    to_merge = []
    num_nodes = len(list(G.nodes()))
    num_edges = len(list(G.edges()))
    coordinates = {}
    gu, gv = None, None
    for u,v,key,data in G.edges(keys=True, data=True):
        if not 'coordinates' in data:
            G.edges[u,v,key]['coordinates'] = [u,v]
            gu, gv = u, v
    #     if data['length'] < MERGING_DIST_THRESHOLD:
    #         to_merge.append((u,v))
    # for u, v in to_merge:
    #     G = nx.contracted_nodes(G, u , v)
    # nx.set_edge_attributes(G, coordinates, name='coordinates')
    # print(nx.get_edge_attributes(G, 'coordinates'))
    # print('check----',G.edges[gu, gv, 0]['coordinates'])
    msg = 'Merged (from {:,} to {:,} nodes and from {:,} to {:,} edges)'
    # print(msg.format(num_nodes, len(list(G.nodes())), num_edges, len(list(G.edges()))))

DEVAULT_OSM_VALUE = {
'width':6,
'lanes':1,
'name':'',
}

DEFAULT_SEGMENT_ATTR = {
'numlanes' : 2,
'capacity' : 1000,
'speedlimit':60,
'category': 2, #linkCat (metadata)--> A,B,C,D,E
'tag':"",
}

DEFAULT_LINK_ATTR = {
'type' : 2,
'category' : 2,
'name': '',
'tags': '',
}

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

def attribute(att_string, sub_attribute, parent_attribute, default_attribute):
    if att_string in sub_attribute:
        return sub_attribute[att_string]
    elif att_string in parent_attribute:
        return parent_attribute[att_string]
    return default_attribute[att_string]

def constructSegments(linkGraph, originalG):
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

        seg = Segment(
                segment_id,
                link_id,
                seq,
                attribute('numlanes', linkToData[link_id], segment_attributes, DEFAULT_SEGMENT_ATTR),
                attribute('capacity', linkToData[link_id], segment_attributes, DEFAULT_SEGMENT_ATTR),
                attribute('speedlimit', linkToData[link_id], segment_attributes, DEFAULT_SEGMENT_ATTR),
                attribute('tag', linkToData[link_id], segment_attributes, DEFAULT_SEGMENT_ATTR),
                attribute('category', linkToData[link_id], segment_attributes, DEFAULT_SEGMENT_ATTR),
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

# def createConnection():



# tempnodeDict = getNodeTypes(G)
# linkGraph = build_linkGraph(G, set(tempnodeDict['uniNodes']))
# mergeClusteringIntersection(linkGraph)
# nodes, links = constructNodesLinks(linkGraph, G, tempnodeDict)
# segments, segToLink, linkToSeg = constructSegments(linkGraph, G)
# linktts = setLinkSegmentAttr(segments, links, linkToSeg)
# print("segments")
# print(segments)

# geoFromPathGraph(linkGraph, G)
# ox.plot_graph(linkGraph)
# print(linkGraph.edges(data=True))
# ox.plot_graph(G)
