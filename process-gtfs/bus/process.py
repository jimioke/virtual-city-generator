import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import Point
from shapely.geometry import MultiPoint
import math
from collections import defaultdict
from process_helper import *


# Use consistent xy coordinate GTFS. Adjust right CRS conversions.
LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}

# PREPARE SIMMOBILITY
# simFolder = 'Auto_sprawl_drive_main/simmobility/'
# gtfsFolder = 'clean-gtfs/Merged/' # 'clean-gtfs/Merged/'
# processFolder = 'process_big/'
# processFolder = 'process_big/'
# oldprocessFolder= 'processing_old/SharedBigger/'

# Small example
simFolder = 'Baltimore_small/simmobility/'
gtfsFolder = 'gtfs_source_small_example/gtfs-QueenAnne/'
processFolder = 'process_small_example/'


# Step 1: Convert segments into graph with end vertices.
# SimMobility segments do not have start and end vertices (nodes).
def getSegment(simFolder=simFolder):
    # Simmobility segment-nodes in lat and long
    segmentGeo = getRoadNetworkGeos(simFolder, fromCRS=LAT_LONG_CRS, toCRS=BALTIMORE_CRS)
    segmentGeo.to_file(processFolder + 'SegmentGeo')
    segmentsWithNodes = getSegmentsWithEndNodes(simFolder, segmentGeo)
    # clean out the same direction (from node, to node)
    # There could be segments whose ends are the same but have different shapes.
    # For understanding, you can comment out the following code and check its shapefile.
    # segmentsWithNodes_duplicated = segmentsWithNodes[segmentsWithNodes.duplicated(['from_node', 'to_node'], keep=False)]
    # print('segmentsWithNodes duplicated (from node, to node) ', len(segmentsWithNodes_duplicated.id.unique()))
    # segmentsWithNodes_duplicated.to_file(processFolder + 'segmentsWithNodes_duplicated')
    segmentsWithNodes.drop_duplicates(subset=['from_node', 'to_node'], inplace=True)
    segmentsWithNodes.to_file(processFolder + 'segmentsWithNodes')


# Step 2: Find segments which are in buffered bus routes.
def findCandidateSegments(bufferSize=50):
    gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df = readGTFS(gtfsFolder,
        trip='trips.txt', stoptime='stop_times.txt', shape='shapes.txt', stop='stops.txt')
    segmentsWithNodes = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    segmentsWithNodes.crs = BALTIMORE_CRS # must be!!
    busStops, busShapes = getBusRouteGeo(gtfs_stop_df, gtfs_shape_df, fromCRS=LAT_LONG_CRS, toCRS=BALTIMORE_CRS)
    busStops.to_file(processFolder + 'busStops')
    busShapes.to_file(processFolder + 'busShapes')
    candidateShapeSegments = findRouteCandidateSegments(segmentsWithNodes, busShapes, processFolder, bufferSize=bufferSize)
    candidateShapeSegments.to_file(processFolder + 'candidateShapeSegments')


# Step 3: Find a start point for each segment. For each bus stop, we find
# the nearest start point because it is computationally faster.
def getSegment_startEndPoint():
    segmentsWithNodes = gpd.read_file(processFolder + 'candidateShapeSegments/candidateShapeSegments.shp')
    segmentsWithNodes['start_point'] =  segmentsWithNodes.apply(lambda row: Point(list(row.geometry.coords)[0]), axis=1)
    segmentEnds = gpd.GeoDataFrame(segmentsWithNodes[['id', 'from_node', 'to_node']], crs=BALTIMORE_CRS, geometry=segmentsWithNodes['start_point'])
    segmentEnds.to_file(processFolder + 'segmentStartPoint')


# Step 4: Find the nearest segment end for each bus stop. (QGIS NNjoin tool)
    # input files: busStops and segmentStartPoint (prefex S)
    # output: stop_to_segmentEnd
    # all in processFolder.


# Step 5: Find a representive segment start for each stop.
# Later we assign a segment based on bus trip connection.
def stop_to_Segment(maxDistance=500):
    stopSegment = gpd.read_file(processFolder + 'busStops/stop_to_segmentEnd.shp')
    stopSegment = stopSegment[['stop_id', 'Sid', 'Sfrom_node', 'Sto_node', 'distance']]
    stopSegment['distance'] = stopSegment['distance'].astype('float')
    stopSegment = stopSegment[stopSegment['distance'] < maxDistance]

    # Keep the nearest segment
    stopSegment.sort_values(by='distance', inplace=True)
    stopSegment = stopSegment.drop_duplicates(subset=['stop_id'], keep='first')
    stopSegment.rename(columns={'Sid':'segment_id', 'Sfrom_node':'from_node', 'Sto_node':'to_node'}, inplace=True)
    stopSegment['str_end_nodes'] = stopSegment.apply(lambda row: str(int(row.from_node)) + '_' + str(int(row.to_node)), axis=1)
    stopSegment.to_csv(processFolder + 'cleaned_stop_segmentEnd.csv')


# Step 6: Find a unique trips which we will construct.
def mainUniqueBusRoutes():
    gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df = readGTFS(gtfsFolder,
        trip='trips.txt', stoptime='stop_times.txt', shape='shapes.txt', stop='stops.txt')
    trip_stops = getUniqueBusRoutes(gtfs_stoptime_df, gtfs_trips_df)
    trip_stops.to_pickle(processFolder + 'trip_stop_sequence.pkl')


# Step 7: Find connected subsequent bus stops
def getConnectedConsequentStops():
    trip_stops = pd.read_pickle(processFolder + 'trip_stop_sequence.pkl')
    candidateShapeSegments = gpd.read_file(processFolder + 'candidateShapeSegments/candidateShapeSegments.shp')
    stopSegmentEnd = pd.read_csv(processFolder + 'cleaned_stop_segmentEnd.csv')
    stopConnection_df = getShortestPath(trip_stops, candidateShapeSegments, stopSegmentEnd)
    stopConnection_df.to_pickle(processFolder + 'connectedStops.pkl')


# Step 8: Construct connected trips
def processConnectedStops():
    # stopConnection = pd.read_csv(processFolder + 'stopConnection.csv')
    stopConnection = pd.read_pickle(processFolder + 'connectedStops.pkl')
    # stopConnection['nodePath'] = stopConnection.apply(lambda row: literal_eval(row.nodePath), axis=1)
    stopConnection.index = stopConnection.apply(lambda row: str(int(row.startStop)) + '_' + str(int(row.endStop)), axis=1)
    connectedStops = stopConnection.index.tolist()
    trip_stops = pd.read_pickle(processFolder + 'trip_stop_sequence.pkl')
    subtrips = []
    stop_to_segment = {}
    for indx, row in trip_stops.iterrows():
        disconnected=False
        conseqStops = list(zip(row.stop_id[:-1], row.stop_id[1:]))
        stop_segmentEnds = []
        path_segmentEnds = []
        path_stops = []
        connected=True
        for s1, s2 in conseqStops:
            string_code = str(s1) + '_' + str(s2)
            if string_code in connectedStops:
                node_sequence =  stopConnection.loc[string_code, 'nodePath']
                if len(node_sequence) > 3: # length must be at least 3
                    stopSeg1 = (node_sequence[0], node_sequence[1])
                    stopSeg2 = (node_sequence[-2], node_sequence[-1])
                    if len(path_stops) == 0:
                        path_stops = [s1,s2]
                        path_segmentEnds += node_sequence
                        stop_segmentEnds += [stopSeg1, stopSeg2]
                    # check if (... from1 -->to) + (from2-->D); fact (from2-->to) exists
                    elif path_segmentEnds[-2] == node_sequence[0]:
                        path_stops.append(s2) # s1 already appended  (... A->B) + (A->C ...) ==> ... A --> C ...
                        path_segmentEnds = path_segmentEnds[:-1] + node_sequence[1:]
                        stop_segmentEnds.append(stopSeg2) # leave the very first node
                    # Untwist # check if (... from1 -->to) + (from2-->D); fact (from2-->to) exists
                    # TODO: check if to --> from2, then simply add to --> from2
                    else:
                        disconnected=True
                else:
                    disconnected=True
            else:
                disconnected=True

            if disconnected:
                if len(path_stops) > 0: # Not connect; start a new trip .
                    subtrips.append((row.trip_id, row.shape_id, path_stops, path_segmentEnds, stop_segmentEnds))
                path_stops = []
                path_segmentEnds = []
                stop_segmentEnds = []
                disconnected = False

    subtrips = pd.DataFrame.from_records(subtrips, columns=['trip_id', 'shape_id', 'stops', 'path_segmentEnds', 'stop_segmentEnds'])
    subtrips['number_stops'] = subtrips.apply(lambda row: len(row.stops), axis=1)
    print('Number of subtrips ', len(subtrips))
    print('Max number of stops ', subtrips.number_stops.max())
    print('Avg number of stops ', subtrips.number_stops.mean())
    subtrips.sort_values(by='number_stops', ascending=False, inplace=True)
    subtrips.to_pickle(processFolder + 'subtrips_found.pkl')
    print(subtrips.head(10))


# Step 9: Express trips in segments as SimMobility requires.
def segmentizeTrips():
    subtrips = pd.read_pickle(processFolder + 'subtrips_found.pkl')
    # gtfs_trips = pd.read_csv(gtfsFolder  + 'trip.csv')
    segmentsWithNodes = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    segmentsWithNodes.index = segmentsWithNodes.apply(lambda row: str(int(row.from_node)) + '_' + str(int(row.to_node)), axis=1)
    def getSegment(ends, row, segmentsWithNodes=segmentsWithNodes):
        ends_string = str(int(ends[0])) + '_' + str(int(ends[1]))
        return segmentsWithNodes.loc[ends_string, 'id']
    subtrips['path_segmentEnds'] = subtrips.apply(lambda row: list(zip(row.path_segmentEnds[:-1], row.path_segmentEnds[1:])), axis=1)
    subtrips['path_segments'] = subtrips.apply(lambda row: [getSegment(end, row) for end in row.path_segmentEnds if end[0] != end[1]], axis=1)
    subtrips['stop_segments'] = subtrips.apply(lambda row: [getSegment(end, row) for end in row.stop_segmentEnds], axis=1)
    subtrips = subtrips[['trip_id', 'shape_id', 'stop_segments', 'path_segments', 'stops']]
    subtrips.to_pickle(processFolder + 'subtrips_wSegments.pkl')


# Step 1: Convert segments into graph with end vertices.
# getSegment()
# # Step 2: Find segments which are in buffered bus routes.
# findCandidateSegments()
# # Step 3: Find a start point for each segment.
# getSegment_startEndPoint()
# # Step 4: Find the nearest segment end for each bus stop. (QGIS NNjoin tool)
#     # input files: busStops and segmentStartPoint (prefex S)
#     # output: stop_to_segmentEnd
#     # all in processFolder.
# # Step 5: Find a representive segment start for each stop.
stop_to_Segment()
# Step 6: Find a unique trips which we will construct.
mainUniqueBusRoutes()
# Step 7: Find connected subsequent bus stops
getConnectedConsequentStops()
# Step 8: Construct connected trips
processConnectedStops()
# Step 9: Express trips in segments as SimMobility requires.
segmentizeTrips()
