import os,csv,pdb
from operator import itemgetter
import math
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
from collections import OrderedDict
import process_osm as posm
from network_elements import*
import xml.etree.ElementTree as ET


class Network:
    def __init__(self, osm_graph):
        self.osm_graph = osm_graph # queried roadnetwork graph from osm
        self.link_graph = None     # node and link graph (all segments combined)
        self.links = None
        self.nodes = None
        self.node_types = None
        self.segments = None # constructed at the final stage
        self.lanes = None
        self.linktts = None

        # Connector and turning paths.
        self.num_connections = 0
        self.connectors = {} # (fromLane, toLane): connector
        self.turnGroups = {} # (fromLink, toLink): turningGroup
        self.turnPaths = {} # (fromLane, toLane): turning paths
        self.numNodes = None
        self.numLinks = None
        self.numSegs = None

    def process_segments_links_nodes(self, clean_intersections=True):
        self.node_types = posm.getNodeTypes(self.osm_graph)
        self.link_graph = posm.build_linkGraph(self.osm_graph, self.node_types['uniNodes'])
        if clean_intersections:
            self.link_graph = posm.clean_intersections(self.link_graph, tolerance=15, dead_ends=False)
        self.nodes, self.links = posm.constructNodesLinks(self.link_graph, self.osm_graph, self.node_types)
        self.segments, segToLink, linkToSeg = posm.constructSegments(self.link_graph, self.osm_graph, SEGMENT_LOWER_BOUND=20)
        self.linktts = posm.setLinkSegmentAttr(self.segments, self.links, linkToSeg)

        for seg, link in segToLink.iteritems():
            self.segments[seg].linkid = link
        for link, seg in linkToSeg.iteritems():
            self.links[link].segments = seg
        print("--------------- {} nodes, {} links and {} segments are constructed -------------------".format(len(self.nodes), len(self.links),len(self.segments)))

    def construct_connections(self, outputFolder, use_SUMO = True):
        if use_SUMO:
            self.construct_turning_paths_from_SUMO(outputFolder)
        else:
            self.construct_default_turning_path()
        self.constructSegmentConnections()

    def construct_default_turning_path(self):
        '''
        '''
        groupcount = 1
        for nodeId, data in self.link_graph.nodes(data=True):
            for fromNode,v1,fromData in self.link_graph.in_edges(nodeId, data=True):
                for v2,toNode,toData in self.link_graph.out_edges(nodeId, data=True):
                    # print("--- ", fromNode,v1, v2,toNode)
                    assert v1 == v2
                    fromLink = fromData['id']
                    toLink = toData['id']
                    fromSeg = self.links[fromLink].segments[-1]
                    toSeg = self.links[toLink].segments[0]

                    if (fromLink,toLink) not in self.turnGroups:
                        self.turnGroups[(fromLink,toLink)] = {'id':groupcount}
                        self.turnGroups[(fromLink,toLink)] = TurningGroup(
                                         id=groupcount,
                                         nodeid=nodeId,
                                         fromlink=fromLink,
                                         tolink=toLink)
                        groupcount +=1

                    maxSpeed = min(self.segments[fromSeg].speedlimit,self.segments[toSeg].speedlimit)
                    for fromLane in range(self.segments[fromSeg].numlanes):
                        fromLaneId =  fromSeg*100 + fromLane
                        for toLane in range(self.segments[toSeg].numlanes):
                            toLaneId = toSeg*100 + toLane
                            groupid = self.turnGroups[(fromLink,toLink)].id
                            firstpoint = self.lanes[fromLaneId].position[-1]
                            secondpoint = self.lanes[toLaneId].position[0]
                            connection = TurningPath(id=self.num_connections,
                                                     from_lane=fromLaneId,
                                                     to_lane=toLaneId,
                                                     group_id=groupid,
                                                     max_speed=maxSpeed,
                                                     position=[firstpoint, secondpoint])
                            self.num_connections += 1
                            #---Constructing the connection polyline
                            self.turnPaths[(fromLaneId,toLaneId)] = connection
        print("-----------------  {} default turning paths constructed  ---------------".format(len(self.turnPaths)))

    def writeSumoShapefile(self, outputFolder):
        # for SUMO
        linkSumoFname = os.path.join(outputFolder,'FILE_map.shp')
        link_data = []
        for id, link in self.links.iteritems():
            points = []
            for seg_id in link.segments:
                points += [(point['x'], point['y']) for point in self.segments[seg_id].position]
            link_data.append((LineString(points), id, str(link.name), link.fromnode, link.tonode, link.speedlimit, link.numlanes))
        df = pd.DataFrame.from_records(link_data, columns=['geometry', 'id', 'name', 'fromnode', 'tonode', 'SPEED', 'rnol'])
        gdf = gpd.GeoDataFrame(df, crs = {'init': 'epsg:4326'}, geometry=df['geometry'])
        gdf.to_file(filename= linkSumoFname)


    def get_turning_paths_from_SUMO(self, outputFolder):
        # prepare SUMO input
        self.writeSumoShapefile(outputFolder)
        # generate turning paths
        os.system("cd " + outputFolder + "; netconvert -v --shapefile-prefix FILE_map -o map.net.xml --shapefile.street-id id --shapefile.from-id fromnode --shapefile.to-id tonode --shapefile.use-defaults-on-failure")
        # parse SUMO output
        tree = ET.parse(outputFolder + '/map.net.xml')
        root = tree.getroot()
        # connSumo = OrderedDict # id: from_lane, to_lane,from_section, to_section, nodeid
        connSumo = []
        for member in root.findall('connection'):
            connData = member.attrib
            if connData['from'][0] != ":":
                fromLink, toLink = int(connData['from']), int(connData['to'])
                nodeid = int(connData['via'].split("_")[0][1:])
                sameNode = (nodeid == self.links[fromLink].tonode and nodeid == self.links[toLink].fromnode)
                if sameNode:
                    tPath = SumoTurnPath(fromLink=fromLink, toLink=toLink, node=nodeid)
                    tPath.fromSeg = self.links[fromLink].segments[-1] # last seg
                    tPath.toSeg = self.links[toLink].segments[0]      # first seg
                    tPath.fromLane = tPath.fromSeg*100 + int(connData['fromLane'])
                    tPath.toLane = tPath.toSeg*100 + int(connData['toLane'])
                    # assert self.links[fromLink].tonode == self.links[toLink].fromnode and self.links[toLink].fromnode == tPath.node
                    connSumo.append(tPath)
        print("-----------------  {} turning paths from SUMO---------------".format(len(connSumo)))
        return connSumo

    def construct_turning_paths_from_SUMO(self, outputFolder):
        '''
        '''
        connSumo = self.get_turning_paths_from_SUMO(outputFolder)
        groupcount = 1
        for p in connSumo:
            # print((p.fromLink, p.toLink))
            if (p.fromLink, p.toLink) not in self.turnGroups:
                # Create turning groups
                turningroup = TurningGroup(id=groupcount, nodeid=p.node, fromlink=p.fromLink, tolink=p.toLink)
                self.turnGroups[(p.fromLink, p.toLink)] = turningroup
                groupcount +=1
            # Create turning path
            maxSpeed = min(self.segments[p.fromSeg].speedlimit, self.segments[p.toSeg].speedlimit)
            groupid = self.turnGroups[(p.fromLink, p.toLink)].id
            # print("line-----", p.fromLane, p.toLane, len(self.lanes))
            position = [self.lanes[p.fromLane].position[-1], self.lanes[p.toLane].position[0]]
            self.turnPaths[(p.fromLane, p.toLane)] = TurningPath(
                    id=self.num_connections,
                    from_lane=p.fromLane,
                    to_lane=p.toLane,
                    group_id=groupid,
                    max_speed=maxSpeed,
                    position=position)
            self.num_connections += 1
        print("-----------------  {} turning groups from SUMO---------------".format(groupcount-1))

    def constructSegmentConnections(self):
        '''
            getConnections() : 1. Constructs the connections from the input connections
                               2. Contructs the polyline for the connections by drawing a straight line from the end of
                                        from 'section' to begining of to section
        '''
        connections = {}
        # connections between segments of the same link
        num_connections_before = self.num_connections
        for linkid,link in self.links.iteritems():
            for seg1,seg2 in zip(link.segments,link.segments[1:]):
                for i in xrange(self.segments[seg1].numlanes):
                    laneid1 = int(seg1)*100 + i
                    for j in xrange(self.segments[seg2].numlanes):
                        laneid2 = int(seg2)*100 + j
                        connKey = (laneid1,laneid2)
                        self.connectors[connKey] = Connector(self.num_connections,laneid1,laneid2,seg1,seg2,)
                        self.num_connections += 1

        print("------------------ {} lane connectors between segments ----------------- ".format(self.num_connections - num_connections_before))

    def write(self,foldername):
        #---Writing nodes
        nodeFname = os.path.join(foldername,'node-nodes.csv')
        with open(nodeFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(['id','x','y','z','traffic_light_id','tags','node_type'])
            nodeList = self.nodes.keys()
            nodeList = sorted([int(item) for item in nodeList])
            for id in nodeList:
                node = self.nodes[id]
                writer.writerow(node.render())

        #---Writing segments
        segFname1 = os.path.join(foldername,'segment-attributes.csv')
        segFname2 = os.path.join(foldername,'segment-nodes.csv')
        with open(segFname1,'wb') as ofile1:
            with open(segFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                segList = self.segments.keys()
                segList = sorted([int(item) for item in segList])
                for id in segList:
                    segment = self.segments[id]
                    writer1.writerow(segment.render())
                    for point in segment.position:
                        aList = [id,point['x'],point['y'],0,point['seq']]
                        writer2.writerow(aList)

        #---Writing segments
        segFname1 = os.path.join(foldername,'segment-attributes_more.csv')
        with open(segFname1,'wb') as ofile1:
            writer1 = csv.writer(ofile1)
            writer1.writerow(['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category','length'])
            segList = self.segments.keys()
            segList = sorted([int(item) for item in segList])
            for id in segList:
                segment = self.segments[id]
                writer1.writerow(segment.render2())

        #---Writing links
        linkFname1 = os.path.join(foldername,'link-attributes.csv')
        linkFname2 = os.path.join(foldername,'link-nodes.csv')
        with open(linkFname1,'wb') as ofile1:
            with open(linkFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','road_type','category','from_node','to_node','road_name','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                linkList = self.links.keys()
                linkList = sorted([int(item) for item in linkList])
                for id in linkList:
                    link = self.links[id]
                    try:
                        writer1.writerow(link.render())
                    except:
                        print("-----unicode", link, link.render())
                    count = 1
                    for segid in link.segments:
                        for point in self.segments[segid].position:
                            aList = [id,point['x'],point['y'],0,count]
                            writer2.writerow(aList)
                            count += 1

        #---Writing lanes
        laneFname1 = os.path.join(foldername,'lane-attributes.csv')
        laneFname2 = os.path.join(foldername,'lane-nodes.csv')
        with open(laneFname1,'wb') as ofile1:
            with open(laneFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','width','vehicle_mode','bus_lane','can_stop','can_park','high_occ_veh','has_road_shoulder','segment','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                laneList = self.lanes.keys()
                laneList = sorted([int(item) for item in laneList])
                for id in laneList:
                    lane = self.lanes[id]
                    writer1.writerow(lane.render())
                    count = 1
                    for point in lane.position:
                        aList = [id,point[0],point[1],0,count]
                        writer2.writerow(aList)
                        count += 1

        #---Writing connections
        #---lane connections first (not turnings)
        connFname = os.path.join(foldername,'connector.csv')
        with open(connFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","from_segment","to_segment","from_lane","to_lane","is_true_connector","tags"])
            connList = [k for k,v in self.connectors.iteritems()]
            connList = sorted([item for item in connList],key=itemgetter(0))
            for id in connList:
                conn = self.connectors[id]
                writer.writerow(conn.render())

        #---Writing turning connections
        turnFname1 = os.path.join(foldername,'turning-attributes.csv')
        turnFname2 = os.path.join(foldername,'turning-nodes.csv')
        with open(turnFname1,'wb') as ofile1:
            with open(turnFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','from_lane','to_lane','group_id','max_speed','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                turnList = [k for k,v in self.turnPaths.iteritems()]
                turnList = sorted([item for item in turnList],key=itemgetter(0))
                for id in turnList:
                    turn = self.turnPaths[id]
                    writer1.writerow(turn.render())
                    count = 1
                    for point in turn.position:
                        aList = [turn.id,point[0],point[1],0,count]
                        writer2.writerow(aList)
                        count += 1

        #---Writing turninggroups
        tgFname = os.path.join(foldername,'turninggroups.csv')
        with open(tgFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","nodeid","from_link","to_link","phases","rules","visibility","tags"])
            tgList = [k for k in self.turnGroups]
            tgList = sorted([item for item in tgList],key=itemgetter(0))
            for id in tgList:
                tg = self.turnGroups[id]
                writer.writerow(tg.render())

        #---Writing default link TTs
        ttFname = os.path.join(foldername,'linkttsdefault.csv')
        with open(ttFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","mode","starttime","endtime","traveltime"])
            linkList = self.linktts.keys()
            linkList = sorted([int(item) for item in linkList])
            for id in linkList:
                linktt = self.linktts[id]
                writer.writerow(linktt.render())

        #---Writing default link TTs
        ttFname = os.path.join(foldername,'linkttsdefault_more.csv')
        with open(ttFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","mode","starttime","endtime","traveltime","length"])
            linkList = self.linktts.keys()
            linkList = sorted([int(item) for item in linkList])
            for id in linkList:
                linktt = self.linktts[id]
                writer.writerow(linktt.render2())

    def writeShapeFiles(self, foldername, write_nodes=True, write_segments=True,
                        write_links=True, write_lanes=True, write_connections=True,
                        write_turningpaths=True):
        #---Writing Node
        if write_nodes:
            nodeFname = os.path.join(foldername,'nodes.shp')
            node_data = OrderedDict()
            for id, node in self.nodes.iteritems():
                node_data[id]=[node.x, node.y, node.type]
            df = pd.DataFrame.from_dict(node_data, orient='index')
            df.columns = ['x', 'y', 'type']
            df['geometry'] = df.apply(lambda row: Point(row.x,row.y),axis=1)
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= nodeFname)

        #---Writing segments
        if write_segments:
            segmentFname = os.path.join(foldername,'segments.shp')
            segment_data = OrderedDict()
            for id, segment in self.segments.iteritems():
                segment_data[id] = LineString([(point['x'], point['y']) for point in segment.position])
            df = pd.DataFrame.from_dict(segment_data, orient='index')
            df.columns = ['geometry'] #['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= segmentFname)

            #---Writing segment coordinates (all coordinates)
            segmentCoordFname = os.path.join(foldername,'segment_coordinates.shp')
            coords = []
            for id, segment in self.segments.iteritems():
                coords += [ Point(point['x'], point['y']) for point in segment.position]
            df = pd.DataFrame.from_dict(coords)
            df.columns = ['geometry']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= segmentCoordFname)

            #---Writing segments' end nodes
            segmentEndsFname = os.path.join(foldername,'segment_end_nodes.shp')
            node_ends = []
            for id, segment in self.segments.iteritems():
                node_ends.append(Point(segment.position[0]['x'], segment.position[0]['y']))
                node_ends.append(Point(segment.position[-1]['x'], segment.position[-1]['y']))
            df = pd.DataFrame.from_dict(node_ends)
            df.columns = ['geometry']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= segmentEndsFname)

        #---Writing links, connecting their segment points. (Segments can represent it)
        if write_links:
            linkFname = os.path.join(foldername,'links.shp')
            link_data = OrderedDict()

            for id, link in self.links.iteritems():
                points = [(self.nodes[link.fromnode].x, self.nodes[link.fromnode].y)]
                for seg_id in link.segments:
                    points += [(point['x'], point['y']) for point in self.segments[seg_id].position]
                points.append((self.nodes[link.tonode].x, self.nodes[link.tonode].y))
                link_data[id] = LineString(points)
            df = pd.DataFrame.from_dict(link_data, orient='index')
            df.columns = ['geometry'] #['id','road_type','category','from_node','to_node','road_name','tags']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= linkFname)

            #---Writing links, connecting their end nodes.
            linkEndsFname = os.path.join(foldername,'connected_link_ends.shp')
            link_ends = OrderedDict()
            for id, link in self.links.iteritems():
                link_ends[id] = LineString([ (self.nodes[link.fromnode].x, self.nodes[link.fromnode].y),
                                               (self.nodes[link.tonode].x, self.nodes[link.tonode].y)])
            df = pd.DataFrame.from_dict(link_ends, orient='index')
            df.columns = ['geometry'] #['id','road_type','category','from_node','to_node','road_name','tags']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= linkEndsFname)

        # #---Writing lanes
        if write_lanes:
            laneFname = os.path.join(foldername,'lanes.shp')
            lane_ends = OrderedDict()
            for id, lane in self.lanes.iteritems():
                lane_ends[id] = LineString([(point[0], point[1]) for point in lane.position])
            df = pd.DataFrame.from_dict(lane_ends, orient='index')
            df.columns = ['geometry'] #['id','road_type','category','from_node','to_node','road_name','tags']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= laneFname)

        #---Writing connections
        #---lane connections first (not turnings)
        if write_connections:
            connFname = os.path.join(foldername,'connector.shp')
            conn_ends = OrderedDict()
            for id, conn in self.connectors.iteritems():
                start = self.lanes[conn.fromlane].position[-1]
                end = self.lanes[conn.tolane].position[0]
                conn_ends[id] = LineString([start, end])

            df = pd.DataFrame.from_dict(conn_ends, orient='index')
            df.columns = ['geometry'] #['id','road_type','category','from_node','to_node','road_name','tags']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= connFname)

            turnFname = os.path.join(foldername,'turningPath.shp')
            turn_ends = OrderedDict()
            for id, conn in self.turnPaths.iteritems():
                start = self.lanes[conn.fromlane].position[-1]
                end = self.lanes[conn.tolane].position[0]
                turn_ends[id] = LineString([start, end])

            df = pd.DataFrame.from_dict(turn_ends, orient='index')
            df.columns = ['geometry'] #['id','road_type','category','from_node','to_node','road_name','tags']
            gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= turnFname)
