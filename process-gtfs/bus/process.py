import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import Point
from shapely.geometry import MultiPoint
import math
from collections import defaultdict
from process_helper2 import *


# Use consistent xy coordinate GTFS. Adjust right CRS conversions.
LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}
TELAVIV_CRS = {'init': 'epsg:2039'}
SINGAPORE_CRS = {'init': 'epsg:3414'}

CURRENT_CRS =  SINGAPORE_CRS #TELAVIV_CRS

# PREPARE SIMMOBILITY
simFolder = 'Auto_sprawl_drive_main/simmobility/'
gtfsFolder = 'clean-gtfs/MergedBus/'
processFolder = 'process_big/'
#
#
# simFolder = '../../network-from-OSM/Outputs/tel_aviv/simmobility_wgs84/'
# gtfsFolder = 'gtfs_clean_israel/bus/'
# processFolder = 'process_tel_aviv/'

# Baltimore
simFolder = 'Auto_sprawl_drive_main/simmobility/'
gtfsFolder = 'clean-gtfs-baltimore/MergedBus/'
processFolder = 'process_baltimore/'

#Singapore
simFolder = '/home/jimi/Dropbox (MIT)/MITei/Research/Prototype-Cities/04-Innovative-Heavyweight-Singapore/Network/simmobility_wgs84/'
gtfsFolder = '/home/jimi/Dropbox (MIT)/MITei/Research/Prototype-Cities/04-Innovative-Heavyweight-Singapore/GTFS/bus/'
processFolder = 'process_innovative_heavyweight/'


# # Small example
# simFolder = 'Baltimore_small/simmobility/'
# gtfsFolder = 'gtfs_source_small_example/gtfs-QueenAnne/'
# processFolder = 'process_small_example/'

# # Small example
# simFolder = 'Baltimore_small/simmobility/'
# gtfsFolder = 'gtfs_source_small_example/gtfs-QueenAnne/'
# processFolder = 'process_small_example/'
# CURRENT_CRS =  BALTIMORE_CRS


def findCandidateSegments(bufferSize=400):
    gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df = readGTFS(gtfsFolder,
        trip='trips.txt', stoptime='stop_times.txt', shape='shapes.txt', stop='stops.txt')
    segmentGeo = getRoadNetworkGeos(simFolder, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS)
    segmentGeo.to_file(processFolder + 'SegmentGeo')
    busStops, busShapes = getBusRouteGeo(gtfs_stop_df, gtfs_shape_df, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS)
    busStops.to_file(processFolder + 'busStops')
    busShapes.to_file(processFolder + 'busShapes')
    candidateShapeSegments = findRouteCandidateSegments(segmentGeo, busShapes, processFolder, bufferSize=bufferSize)
    candidateShapeSegments.to_file(processFolder + 'candidateSegments')

def findCandidateSegments(bufferSize=400):
    gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df = readGTFS(gtfsFolder,
        trip='trips.txt', stoptime='stop_times.txt', shape='shapes.txt', stop='stops.txt')
    segmentGeo = getRoadNetworkGeos(simFolder, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS)
    segmentGeo.to_file(processFolder + 'SegmentGeo')
    busStops, busShapes = getBusRouteGeo(gtfs_stop_df, gtfs_shape_df, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS)
    busStops.to_file(processFolder + 'busStops')
    busShapes.to_file(processFolder + 'busShapes')
    candidateShapeSegments = findRouteCandidateSegments(segmentGeo, busShapes, processFolder, bufferSize=bufferSize)
    candidateShapeSegments.to_file(processFolder + 'candidateSegments')

# Step 1: Convert segments into graph with end vertices.
# SimMobility segments do not have start and end vertices (nodes).
def getSegment(simFolder=simFolder):
    # Simmobility segment-nodes in lat and long
    segmentGeo = gpd.read_file(processFolder + 'candidateSegments/candidateSegments.shp')
    segmentsWithNodes = getSegmentsWithEndNodes(simFolder, segmentGeo, CURRENT_CRS)
    # clean out the same direction (from node, to node)
    # There could be segments whose ends are the same but have different shapes.
    # For understanding, you can comment out the following code and check its shapefile.
    # segmentsWithNodes_duplicated = segmentsWithNodes[segmentsWithNodes.duplicated(['from_node', 'to_node'], keep=False)]
    # print('segmentsWithNodes duplicated (from node, to node) ', len(segmentsWithNodes_duplicated.id.unique()))
    # segmentsWithNodes_duplicated.to_file(processFolder + 'segmentsWithNodes_duplicated')
    segmentsWithNodes.drop_duplicates(subset=['ends'], inplace=True)
    segmentsWithNodes.to_file(processFolder + 'segmentsWithNodes')
    # 'id', 'link_id', 'sequence', 'num_lanes', 'capacity', 'max_speed',
    #    'tags', 'link_category', 'length', 'from_node', 'to_node', 'ends',
    #    'geometry'
# getSegment()


# Step 3: Find a start point for each segment. For each bus stop, we find
# the nearest start point because it is computationally faster.
def getSegment_startEndPoint():
    segmentsWithNodes = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    segmentsWithNodes['start_point'] =  segmentsWithNodes.apply(lambda row: Point(list(row.geometry.coords)[0]), axis=1)
    segmentEnds = gpd.GeoDataFrame(segmentsWithNodes[['id', 'from_node', 'to_node']], crs=CURRENT_CRS, geometry=segmentsWithNodes['start_point'])
    segmentEnds.to_file(processFolder + 'segmentStartPoint')
    # Present segments by their start point


# Step 4: Find the nearest segment end for each bus stop. (QGIS NNjoin tool)
    # input files: busStops and segmentStartPoint (prefex S)
    # output: stop_to_segmentEnd or busStops_segmentStartPoint
    # all in processFolder.


# Step 5: Find a representive segment start for each stop.
# Later we assign a segment based on bus trip connection.
def stop_to_Segment(maxDistance=400):
    # stopSegment = gpd.read_file(processFolder + 'busStops/busStops_segmentStartPoint.shp')
    stopSegment = gpd.read_file(processFolder + 'busStops/stop_to_segmentStart.shp')

    stopSegment = stopSegment[['stop_id', 'Sid', 'Sfrom_node', 'Sto_node', 'distance']]
    stopSegment['distance'] = stopSegment['distance'].astype('float')
    stopSegment = stopSegment[stopSegment['distance'] < maxDistance]

    # Keep the nearest segment
    stopSegment.sort_values(by='distance', inplace=True)
    stopSegment = stopSegment.drop_duplicates(subset=['stop_id'], keep='first')
    stopSegment.rename(columns={'Sid':'segment_id', 'Sfrom_node':'from_node', 'Sto_node':'to_node'}, inplace=True)
    stopSegment['str_end_nodes'] = stopSegment.apply(lambda row: str(int(row.from_node)) + '_' + str(int(row.to_node)), axis=1)
    stopSegment.to_csv(processFolder + 'cleaned_stop_segmentEnd.csv')
    print(stopSegment.columns)
    # Index(['stop_id', 'segment_id', 'from_node', 'to_node', 'distance', 'str_end_nodes']
# stop_to_Segment()

# Step 6: Find a unique trips which we will construct.
def mainUniqueBusRoutes():
    gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df = readGTFS(gtfsFolder,
        trip='trips.txt', stoptime='stop_times.txt', shape='shapes.txt', stop='stops.txt')
    trip_stops = getUniqueBusRoutes(gtfs_stoptime_df, gtfs_trips_df)
    trip_stops.to_pickle(processFolder + 'trip_stop_sequence.pkl')


# Step 7: Find connected subsequent bus stops
def getConnectedConsequentStops():
    trip_stops = pd.read_pickle(processFolder + 'trip_stop_sequence.pkl')
    candidateShapeSegments = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    stopSegmentEnd = pd.read_csv(processFolder + 'cleaned_stop_segmentEnd.csv')
    stopConnection_df = getShortestPath(trip_stops, candidateShapeSegments, stopSegmentEnd)
    stopConnection_df.to_pickle(processFolder + 'connectedStops.pkl')

def processConnectedStops():
    stopConnection = pd.read_pickle(processFolder + 'connectedStops.pkl')
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
                    if s2 in stop_to_segment:
                        assert(stop_to_segment[s2] == stopSeg2)
                        # TODO: If assert fails, make it disconnected.
                    stop_to_segment[s2] = stopSeg2
                    if len(path_stops) == 0: # first
                        path_stops = [s1,s2]
                        path_segmentEnds += node_sequence
                        stop_segmentEnds += [stopSeg1, stopSeg2] # Very first segment might change
                    # check if (... from1 -->to) + (from2-->D); fact (from2-->to) exists
                    else:
                        if path_segmentEnds[-1] != node_sequence[0] or path_stops[-1] != s1:
                            print('\n path_segmentEnds ', path_segmentEnds)
                            print('\n path_stops ', path_stops)
                            print('\n stops s1, s2', s1, s2)
                            print('\n node_sequence btwn s1, s2', node_sequence)
                            print('\n stop seg stopSeg1, stopSeg2', stopSeg1, stopSeg2)


                        assert(path_segmentEnds[-1] == node_sequence[0])
                        assert(path_stops[-1] == s1)
                        path_stops.append(s2)
                        path_segmentEnds += node_sequence[1:]
                        # stop_segmentEnds[-1] = stopSeg1
                        stop_segmentEnds.append(stopSeg2)
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
    for i, row in subtrips.iterrows():
        if row.stops[0] in stop_to_segment:
            first_stop_segEnds = stop_to_segment[row.stops[0]]
            subtrips.loc[i, "stop_segmentEnds"] = [first_stop_segEnds] + row.stop_segmentEnds[1:]
            subtrips.loc[i, "path_segmentEnds"] = [first_stop_segEnds[0]] + row.path_segmentEnds

    subtrips['number_stops'] = subtrips.apply(lambda row: len(row.stops), axis=1)
    print('Number of subtrips ', len(subtrips))
    print('Max number of stops ', subtrips.number_stops.max())
    print('Avg number of stops ', subtrips.number_stops.mean())
    subtrips.to_pickle(processFolder + 'subtrips_found.pkl')

# Step 9: Express trips in segments as SimMobility requires.
def segmentizeTrips():
    subtrips = pd.read_pickle(processFolder + 'subtrips_found.pkl')
    segmentsWithNodes = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    segmentsWithNodes.drop_duplicates(subset=['ends'], inplace=True)
    segmentsWithNodes.to_csv(processFolder + 'candidateShapeSegments.csv')
    segmentsWithNodes.index = segmentsWithNodes.ends
    def getSegment(ends, row, segmentsWithNodes=segmentsWithNodes):
        ends_string = str(int(ends[0])) + '_' + str(int(ends[1]))
        return segmentsWithNodes.loc[ends_string, 'id']
    subtrips['path_segmentEnds'] = subtrips.apply(lambda row: list(zip(row.path_segmentEnds[:-1], row.path_segmentEnds[1:])), axis=1)
    def segmentize(segmentEnds):
        segments = []
        for ends in segmentEnds:
            ends_string = str(int(ends[0])) + '_' + str(int(ends[1]))
            s = segmentsWithNodes.loc[ends_string, 'id']
            segments.append(s)
        return segments

    subtrips['path_segments'] = subtrips.apply(lambda row:segmentize(row.path_segmentEnds), axis=1)
    subtrips['stop_segments'] = subtrips.apply(lambda row: [getSegment(end, row) for end in row.stop_segmentEnds], axis=1)
    print(subtrips[['path_segments', 'path_segmentEnds']])
    subtrips.to_csv(processFolder + 'subtrips_wSegments_full.csv', index=False)
    subtrips = subtrips[['trip_id', 'shape_id', 'stop_segments', 'path_segments', 'stops']]
    subtrips.to_pickle(processFolder + 'subtrips_wSegments.pkl')

def test():
    subtrips = pd.read_pickle(processFolder + 'subtrips_found.pkl')
    print(subtrips.head(10))
# test()


print('Step 1: Find segments which are in buffered bus routes.')
findCandidateSegments()

print('Step 2: Convert segments into graph with end vertices.')
getSegment()

print('Step 3: Find a start point for each segment.')
getSegment_startEndPoint()

def test():
    subtrips = pd.read_pickle(processFolder + 'subtrips_found.pkl')
    print(subtrips.head(10))


# print('Step 1: Find segments which are in buffered bus routes.')
# findCandidateSegments()
# #
# print('Step 2: Convert segments into graph with end vertices.')
# getSegment()
#
# print('Step 3: Find a start point for each segment.')
# getSegment_startEndPoint()
# # Step 4: Find the nearest segment end for each bus stop. (QGIS NNjoin tool)
#     # input files: busStops and segmentStartPoint in processFolder ( add prefex 'S')
#     # output: stop_to_segmentEnd
#     # all in processFolder.

# print('Step 5: Find a representive segment start for each stop.')
# stop_to_Segment()
#
# print('Step 6: Find a unique trips which we will construct.')
# mainUniqueBusRoutes()

# print('Step 7: Find connected subsequent bus stops')
# getConnectedConsequentStops()
#
# print('Step 8: Construct connected trips')
# processConnectedStops()
#
# print('Step 9: Express trips in segments as SimMobility requires.')
# segmentizeTrips()
