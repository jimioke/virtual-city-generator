import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import transform
import matplotlib.pyplot as plt
from shapely.ops import nearest_points


def constructSeqLine(df, idColumn='id', seqColumn='seq_id', x='x', y='y'):
    df = df.sort_values([seqColumn])
    grouped = df.groupby(idColumn)
    rows = []
    for name,group in grouped:
        line_coords = group[[x, y]]
        line = LineString(tuple(x) for x in line_coords.to_records(index=False))
        rows.append( (name, line) )
    return pd.DataFrame.from_records(rows, columns=[idColumn, 'geometry'])

def readGTFS(gtfsFolder, trip='trip.csv', stoptime='stoptime.csv', shape='shape.csv', stop='stops.csv'):
    # read
    gtfs_trips_df = pd.read_csv(gtfsFolder  + trip)
    gtfs_stoptime_df = pd.read_csv(gtfsFolder  + stoptime)
    gtfs_shape_df = pd.read_csv(gtfsFolder + shape)
    gtfs_stop_df = pd.read_csv(gtfsFolder + stop)
    # gtfs_stop_df = pd.read_csv(gtfsFolder + 'stops.txt')
    return gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df

def getRoadNetworkGeos(simFolder, fromCRS, toCRS):
    # segmentCoords = pd.read_csv(simFolder + 'segment-nodes.csv') #id,x,y,z,seq_id
    segmentCoords = pd.read_csv(simFolder + 'segment_polyline.csv')
    segmentGeo = constructSeqLine(segmentCoords)
    segmentGeo = gpd.GeoDataFrame(segmentGeo, crs=fromCRS)
    segmentGeo = segmentGeo.to_crs(toCRS)
    return segmentGeo

def getBusRouteGeo(busStops, busShapes, fromCRS, toCRS):
    busStopGeo = [Point(xy) for xy in zip(busStops.stop_lon, busStops.stop_lat)]
    busStopGeo = gpd.GeoDataFrame(busStops, crs=fromCRS, geometry=busStopGeo)
    busStopGeo = busStopGeo.to_crs(toCRS)
    busShapeGeo = constructSeqLine(busShapes, idColumn= 'shape_id', seqColumn='shape_pt_sequence', x='shape_pt_lon', y='shape_pt_lat')
    busGeo = gpd.GeoDataFrame(busShapeGeo, crs=fromCRS)
    busGeo = busGeo.to_crs(toCRS)
    return busStopGeo, busGeo

def getSegmentsWithEndNodes(simFolder, candidateSegment, CRS, base = 10000000):
    # turningPaths = pd.read_csv(simFolder + 'turning-attributes.csv')  #id,from_lane,to_lane,group_id,max_speed,tags
    turningPaths = pd.read_csv(simFolder + 'turning_path.csv')
    turningPaths["from_segment"] = turningPaths["from_lane"] // 100
    turningPaths["to_segment"] = turningPaths["to_lane"] // 100
    connector = pd.read_csv(simFolder + 'connector.csv') #id,from_segment,to_segment,from_lane,to_lane,is_true_connector,tags

    connectSegments = list(zip(turningPaths.from_segment, turningPaths.to_segment))
    connectSegments += list(zip(connector.from_segment, connector.to_segment))

    # Not necessary to include the following code since turning paths and connectors are enough.
    # segments = segments.sort_values(['id'])
    # segSequence = segments.groupby('link_id')['id'].apply(list).tolist()
    # for seq in segSequence:
    #     if len(seq) > 1:
    #         connectSegments += list(zip(seq[:-1],seq[1:]))

    fromPoint = {} # seg --> node
    toPoint = {}
    NODE_ID = 1
    candidateSegIDs = set(candidateSegment.id.tolist())
    # Create nodes between segments    fromPoint --> seg1 --> (toPoint) = (fromPoint) --> seg2
    for seg1, seg2 in  connectSegments:
        # We are interested in only candidate segments
        if seg1 in candidateSegIDs and seg2 in candidateSegIDs:
            if seg1 in toPoint and seg2 in fromPoint:
                assert(toPoint[seg1] == fromPoint[seg2])
            elif seg1 in toPoint:
                fromPoint[seg2] = toPoint[seg1]
            elif seg2 in fromPoint:
                toPoint[seg1] = fromPoint[seg2]
            else:
                toPoint[seg1] = fromPoint[seg2] = NODE_ID
                NODE_ID += 1
    # Have to give nodes for dead ends
    for seg in candidateSegIDs:
        if seg not in toPoint: # seg --> toPoint --> None
            toPoint[seg] = NODE_ID
            NODE_ID += 1
        if seg not in fromPoint: # None --> fromPoint --> seg
            fromPoint[seg] = NODE_ID
            NODE_ID += 1

    print('MAX Node id ', NODE_ID)

    candidateSegment['from_node'] = candidateSegment.apply(lambda row: fromPoint[int(row.id)] if int(row.id) in fromPoint else row.link_id * base + row.sequence - 1, axis=1)
    candidateSegment['to_node'] = candidateSegment.apply(lambda row: toPoint[int(row.id)] if int(row.id) in toPoint else row.link_id * base + row.sequence, axis=1)
    candidateSegment['from_node'] = candidateSegment['from_node'].astype('int')
    candidateSegment['to_node'] = candidateSegment['to_node'].astype('int')
    candidateSegment['ends'] = candidateSegment.apply(lambda row: str(int(row.from_node)) + '_' + str(int(row.to_node)), axis=1)
    print("Number of segments and unique ends: ", len(candidateSegment), len(candidateSegment.ends.unique()))
    return candidateSegment

def  findRouteCandidateSegments(segmentsWithNodes, busShapes, processFolder, bufferSize=50):
    busShapes['geometry'] = busShapes['geometry'].buffer(distance=bufferSize)
    candidateShapeSegments = gpd.sjoin(segmentsWithNodes,busShapes, op='intersects')
    # candidateShapeSegments.to_file(processFolder + 'busShape')
    return candidateShapeSegments

def getUniqueBusRoutes(stoptime_df, trips_df):
    trips_df.drop_duplicates(subset=['shape_id'], inplace=True)
    unique_trips = trips_df.trip_id.unique()
    stoptime_df = stoptime_df[stoptime_df.trip_id.isin(unique_trips)]
    stoptime_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)
    trip_stops = stoptime_df.groupby('trip_id')['stop_id'].apply(list).to_frame()
    trip_stops = trip_stops.reset_index()
    trip_stops = trip_stops.merge(trips_df[['trip_id', 'shape_id']], on='trip_id', how='left')
    print('Unique trips ', len(unique_trips))
    return trip_stops

def getShortestPath(trip_stops, shapeSegments, stopSegmentEnd):
    stopSegmentEnd.index = stopSegmentEnd.stop_id
    valid_stops = stopSegmentEnd[stopSegmentEnd['distance'] < 500].stop_id.tolist()

    stopConnectionSet = set()
    stopConnection_df = []
    num_no_connection = 0
    for indx, trip in trip_stops.iterrows():
        print('trip being.. ', indx)
        # Filter trip route segments
        routeSegments = shapeSegments[shapeSegments['shape_id'] == trip.shape_id]
        # print('routeSegments', len(routeSegments))
        edgeList = list(zip(routeSegments['from_node'], routeSegments['to_node']))
        G = nx.MultiDiGraph()
        G.add_edges_from(edgeList)

        # Search connection between consequent stops
        consequentStops = zip(trip.stop_id[:-1], trip.stop_id[1:])
        for startStop, endStop in consequentStops:
            # print(startStop, endStop)
            if ((startStop, endStop) not in stopConnectionSet) and (startStop in valid_stops) and (endStop in valid_stops):
                startNode = stopSegmentEnd.loc[startStop, 'from_node']
                endNode = stopSegmentEnd.loc[endStop ,'to_node']
                if startNode in G and endNode in G:
                    try:
                        nodePath = nx.shortest_path(G, source=startNode, target=endNode)
                        stopConnectionSet.add((startStop, endStop))
                        stopConnection_df.append((startStop, endStop, nodePath))
                    except nx.exception.NetworkXNoPath:
                        # print('No connection in between ', startStop, endStop)
                        num_no_connection += 1
                        pass
    print('Number of no connection ', num_no_connection)
    stopConnection_df = pd.DataFrame.from_records(stopConnection_df, columns=['startStop', 'endStop', 'nodePath'])
    return stopConnection_df
