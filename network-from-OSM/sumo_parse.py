import xml.etree.ElementTree as ET
from network import*
from network_elements import*

inputFolder = "sumo_input_files"
outputFolder = "sumo_outputs"
treeEdge = ET.parse(inputFolder + '/Boston.edg.xml')
rootEdge = treeEdge.getroot()

treeNode = ET.parse(inputFolder + '/Boston.nod.xml')
rootNode = treeNode.getroot()

drivable_types = ['highway.secondary', 'highway.secondary', "highway.motorway"]

trafficLightId = 1
netOffsetX = -327868.90
netOffsetY = -4691698.75
# connSumo = OrderedDict # id: from_lane, to_lane,from_section, to_section, nodeid
edges = []
links = {}
nodes = {}
lanes = {}
for member in rootNode.findall('node'):
    data = member.attrib
    # print(member)
    if 'id' in data and data['id'] not in nodes:
        trafficLightId = 0
        if (data['type'] == 'traffic_light'):
            traffic_light = trafficLightId
            trafficLightId += 1
            # (self,id,type,tLightId,x,y,z=0)
        nodes[data['id']] = Node(
                id=data['id'],
                type=0,
                tLightId=trafficLightId,
                x=float(data['x']),
                y=float(data['y']))

print("----nodes", len(nodes))
unknownNodes = 0
for member in rootEdge.findall('edge'):
    data = member.attrib
    if 'from' in data and 'to' in data and 'shape' in data:
        if data['id'] not in links and data['type'] in drivable_types:
            # (self,id,roadtype,category,upnode,dnnode,name,numlanes,speedlimit,segments = None):
            raw_shape = [ coord.split(',') for coord in data['shape'].split(" ")]
            shape = [ (float(coord[0]), float(coord[1])) for coord in raw_shape]
            links[data['id']] = Link(
                id=data['id'],
                roadtype=1,
                category=1,
                upnode=data['from'],
                dnnode=data['to'],
                name='',
                numlanes=int(data['numLanes']),
                speedlimit=float(data['speed']),
                segments=shape
            )
        if data['from'] not in nodes or data['to'] not in nodes:
            # print("weird end")
            unknownNodes += 1
        for lane in member:
            # (self,id,segid,width,vehiclemode=None,buslane=0,canstop=0,canpark=0,hov=0,hasshoulder=0,position=None):
            ldata = lane.attrib
            lanes[ldata['id']] =  Lane(
                id=ldata['id'],
                segid=0,
                width=12,
                position=ldata['shape']
            )


print("----links", len(links), unknownNodes)
print("----lanes", len(lanes))


nodeFname = os.path.join(outputFolder,'nodes.shp')
node_data = OrderedDict()
for id, node in nodes.iteritems():
    node_data[id]=[node.x, node.y, node.type]
df = pd.DataFrame.from_dict(node_data, orient='index')
df.columns = ['x', 'y', 'type']
df['geometry'] = df.apply(lambda row: Point(row.x,row.y),axis=1)
gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
gdf.to_file(driver = 'ESRI Shapefile', filename= nodeFname)


segmentFname = os.path.join(outputFolder,'segments.shp')
segment_data = OrderedDict()
for id, segment in links.iteritems():
    # print(segment.segments)
    segment_data[id] = LineString([(point[0], point[1]) for point in segment.segments])
df = pd.DataFrame.from_dict(segment_data, orient='index')
df.columns = ['geometry'] #['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category']
gdf = gpd.GeoDataFrame(df, geometry = df.geometry)
gdf.to_file(driver = 'ESRI Shapefile', filename= segmentFname)


# filters['drive'] = ('["area"!~"yes"]["highway"!~"cycleway|footway|path|pedestrian|steps|track|'
#                     'proposed|construction|bridleway|abandoned|platform|raceway|service"]'
#                     '["motor_vehicle"!~"no"]["motorcar"!~"no"]["access"!~"private"]'
#                     '["service"!~"parking|parking_aisle|driveway|private|emergency_access"]')
#


    # print(data)
    # for c in member:
    #     print(c)
    # # print(member.attrib)
    # # print(member.tag)
    # print("ok")
    # for child in member:
    #     print(child.tag, child.attrib)
    # edgeData = member.attrib
    # links[edgeData['id']]

    # edges.append(edgeData)
# print(edges[0])
