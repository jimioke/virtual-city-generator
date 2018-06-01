import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import Point
from shapely.geometry import MultiPoint
import math
from collections import defaultdict
# from ast import literal_eval
import datetime

BUS_SPEED = 10
 # New York in 2013 was 9.5 mph, while Phoenix's buses traveled at a much faster 12.2 mph
LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}
TELAVIV_CRS = {'init': 'epsg:2039'}


# PREPARE SIMMOBILITY
simFolder = 'Auto_sprawl_drive_main/simmobility/'
gtfsFolder = 'clean-gtfs/MergedBus/'
processFolder = 'process_big/'
databaseFolder = 'to_db_big/'
CURRENT_CRS =  BALTIMORE_CRS

# Tel Aviv
# simFolder = '../../network-from-OSM/Outputs/tel_aviv/simmobility_wgs84/'
# gtfsFolder = 'gtfs_clean_israel/bus/'
# processFolder = 'process_tel_aviv/'
# databaseFolder = 'to_db_tel_aviv/'
# CURRENT_CRS = TELAVIV_CRS

# Small example
# simFolder = 'Baltimore_small/simmobility/'
# gtfsFolder = 'gtfs_source_small_example/gtfs-QueenAnne/'
# processFolder = 'process_small_example/'
# databaseFolder = 'to_db/'

# SimMobility table headers
bus_stops_cols = ['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']
pt_bus_stops_cols = ['route_id', 'stop_code', 'sequence_no']
pt_bus_routes_cols = ['route_id', 'sequence_no', 'section_id']
frequence_cols = ['frequency_id', 'line_id', 'start_time', 'end_time', 'headway_sec']
journey_cols = ['service_id', 'trip_id', 'stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'dwelling_time']


# Prune out bus stop sequences
def pruneShortTrips(connectedTrips=None):
    connectedTrips = pd.read_pickle(processFolder + 'subtrips_wSegments.pkl')
    connectedTrips['len_stops'] = connectedTrips.apply(lambda row: len(row.stops), axis=1)
    connectedTrips['len_uniq_stops'] = connectedTrips.apply(lambda row: len(set(row.stops)), axis=1)
    print('Number of the same segment consequent stops')
    print(len(connectedTrips[connectedTrips.len_stops != connectedTrips.len_uniq_stops]))
    connectedTrips['len_path_in_seg'] = connectedTrips.apply(lambda row: len(row.path_segments), axis=1)
    print("stops ---------------")
    print(connectedTrips.len_stops.value_counts())
    connectedTrips = connectedTrips[connectedTrips.len_stops == connectedTrips.len_uniq_stops]
    connectedTrips= connectedTrips[connectedTrips.len_stops > 3]
    print("stops ---------------")
    print(connectedTrips.len_stops.value_counts())
    print("all stops -----")
    print(connectedTrips.len_stops.sum())
    return connectedTrips


# Create pt_bus_routes and pt_bus_stops and pre prepare bus_stops.
def createBusRouteTables():
    """
    Based on connected subtrips, prepare unique stop sequence routes (we already filterred out shapes).
            pt_bus_routes:  ['route_id', 'sequence_no', 'section_id']
            pt_bus_stops:   ['route_id', 'stop_code', 'sequence_no', 'trip_id']
            pre_bus_stops:  ['id', 'section_id', 'terminal', 'stop_code'] One to one (stop to segment)
    """
    # [['trip_id', 'shape_id', 'stop_segments', 'path_segments', 'stops']]
    # connectedTrips = pd.read_pickle(processFolder + 'subtrips_wSegments.pkl')
    connectedTrips = pruneShortTrips()
    # connectedTrips.to_csv(processFolder + 'test_subtrips_wSegments.csv', index=False)
    connectedTrips['segment_seq'] = connectedTrips.apply(lambda row: '_'.join([str(s) for s in row.stop_segments]), axis=1)
    connectedTrips.drop_duplicates(subset=['segment_seq'], inplace=True)
    connectedTrips = connectedTrips.reset_index()
    connectedTrips['route_id'] = connectedTrips.index + 1
    connectedTrips['route_id'] = connectedTrips.apply(lambda row: 'BL_' + str(row.route_id) + '_1', axis=1)

    bus_stops_df = []
    pt_bus_stops_df = []
    pt_bus_routes_df = []
    terminal_stops = set()
    for indx, trip in connectedTrips.iterrows():
        # terminal_stops.add(trip.stops[0])
        terminal_stops.add(trip.stops[-1]) # TODO CHECK
        for i, i_stop in enumerate(trip.stops):
            i_segment = trip.stop_segments[i]
            bus_stops_df.append((i_stop, i_segment))
            pt_bus_stops_df.append( (trip.route_id, i_stop, i, trip.trip_id))
        for i, seg in enumerate(trip.path_segments):
            pt_bus_routes_df.append( (trip.route_id, i, seg))

    pt_bus_stops_df = pd.DataFrame.from_records(pt_bus_stops_df, columns=['route_id', 'stop_code', 'sequence_no', 'trip_id'])
    pt_bus_routes_df = pd.DataFrame.from_records(pt_bus_routes_df, columns=['route_id', 'sequence_no', 'section_id'])
    bus_stops_df = pd.DataFrame.from_records(bus_stops_df, columns=['id', 'section_id'])
    bus_stops_df['terminal'] = bus_stops_df.apply(lambda row: int(row.id in terminal_stops), axis=1)

    # Unite the stops that are assigned to the same segment
    bus_stops_df['id'] = bus_stops_df['id'].astype(int)
    bus_stops_df['section_id'] = bus_stops_df['section_id'].astype(int)
    pt_bus_stops_df['stop_code'] = pt_bus_stops_df['stop_code'].astype(int)
    stop_to_RepStop = {}
    segment_to_stop = {}
    for index, row in bus_stops_df.iterrows():
        if row.section_id not in segment_to_stop:
            segment_to_stop[row.section_id] = row.id
        stop_to_RepStop[row.id] = segment_to_stop[row.section_id]
    stop_ids = set(stop_to_RepStop.values()) # Representive stops
    bus_stops_df = bus_stops_df[bus_stops_df.id.isin(stop_ids)]
    pt_bus_stops_df['stop_code'] = pt_bus_stops_df.apply(lambda row: stop_to_RepStop[row.stop_code], axis=1)

    pt_bus_stops_df.to_csv(processFolder + 'pre_pt_bus_stops.csv')
    pt_bus_stops_df[['route_id', 'stop_code', 'sequence_no']].to_csv(databaseFolder + 'pt_bus_stops.csv', index=False)
    pt_bus_routes_df.to_csv(databaseFolder + 'pt_bus_routes.csv', index=False)
    bus_stops_df.to_csv(databaseFolder + 'pre_bus_stops.csv', index=False)
    connectedTrips.to_pickle(processFolder + 'unique_subtrips_wSegments.pkl')


def getRouteSegment():
    pt_bus_routes = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')
    segments = gpd.read_file(processFolder + 'candidateShapeSegments/candidateShapeSegments.shp')
    print(segments.columns)
    pt_bus_routes = pt_bus_routes.merge(segments, left_on='section_id', right_on='id')
    route_segments = gpd.GeoDataFrame(pt_bus_routes, crs=CURRENT_CRS, geometry=pt_bus_routes['geometry'])
    route_segments.to_file(processFolder + 'routeSegmentGeo')


def get_stops_xy():
    busStopGeo = gpd.read_file(processFolder + 'BusStops/BusStops.shp')
    busStopGeo['x'] = busStopGeo.apply(lambda row: row['geometry'].x, axis=1)
    busStopGeo['y'] = busStopGeo.apply(lambda row: row['geometry'].y, axis=1)
    busStops = busStopGeo[['stop_id', 'x', 'y', 'stop_name']]
    busStops.to_csv(processFolder  + 'stops_xy.csv')
# get_stops_xy()

def getSegmentSinkNodes(simFolder):
    links = pd.read_csv(simFolder + 'link-attributes.csv') #id,road_type,category,from_node,to_node,road_name,tags,osmid
    links.rename(columns={'id':'link_id'}, inplace=True)
    segments = pd.read_csv(simFolder + 'segment-attributes.csv') #id,link_id,sequence,num_lanes,capacity,max_speed,tags,link_category
    segments = pd.merge(segments, links[['link_id', 'to_node']], on=['link_id'])
    return segments[['id', 'to_node']]

def complete_bus_stops():
    """
    Based on pre_bus_stops ['id', 'section_id', 'terminal', 'stop_code']
    Complete bus_stops ['x', 'y', 'z', 'id', 'code', 'section_id', 'name',
                    'status', 'terminal', 'length', 'section_offset', 'tags',
                    'reverse_section', 'terminal_node']
    """
    segments = gpd.read_file(processFolder + 'SegmentGeo/SegmentGeo.shp')
    print('segments geo', segments.columns)
    segments.id = segments.id.astype(int)

    segments.index = segments.id
    # print(segments.index.tolist())
    # print(78348 in segments.index.tolist())
    segments['half_length'] = segments.apply(lambda row: row.geometry.length/2, axis=1)
    segments['seg_middle_point'] = segments.apply(lambda row: row.geometry.interpolate(0.5, normalized=True), axis=1)
    bus_stops_df = pd.read_csv(databaseFolder + 'pre_bus_stops.csv')
    bus_stops_df.id = bus_stops_df.id.astype(int)
    # bus_stops_df.section_id = bus_stops_df.section_id.astype(int)
    print(bus_stops_df.head(10))
    bus_stops_df.section_id = bus_stops_df.section_id.astype(int)
    bus_stops_df.drop_duplicates(subset=['id'], inplace=True)
    bus_stops_df.sort_values(by='id', inplace=True)
    bus_stops_df['stop_code'] = bus_stops_df['id']
    bus_stops_df['code'] = bus_stops_df["id"]
    bus_stops_df['section_offset'] = bus_stops_df.apply(lambda row: segments.loc[row.section_id, 'half_length'], axis=1)
    bus_stops_df['seg_middle_point'] = bus_stops_df.apply(lambda row: segments.loc[row.section_id, 'seg_middle_point'], axis=1)
    bus_stops_df['x'] = bus_stops_df.apply(lambda row: row.seg_middle_point.x, axis=1)
    bus_stops_df['y'] = bus_stops_df.apply(lambda row: row.seg_middle_point.y, axis=1)
    bus_stops_df["status"] = "OP"
    bus_stops_df["z"] = 0
    bus_stops_df["length"] = 8 # Boston default
    bus_stops_df["tags"] = ""
    bus_stops_df['terminal'] = 0
    bus_stops_df['terminal_node'] = 0
    bus_stops_df['reverse_section'] = 0
    bus_stops_df['name'] = ''

    bus_stops_df = bus_stops_df[['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']]
    bus_stops_df.to_csv(databaseFolder + 'bus_stop.csv', index=False)

    print('Number of unique stops ', len(bus_stops_df.id.unique()))
    print('Number of stops ', len(bus_stops_df))


def lat_long_stops():
    stops = pd.read_csv(databaseFolder + 'bus_stop.csv')
    coords = [Point(xy) for xy in zip(stops.x, stops.y)]
    stops = gpd.GeoDataFrame(stops, crs=CURRENT_CRS, geometry=coords)
    stops = stops.to_crs(LAT_LONG_CRS)
    stops['x'] = stops['geometry'].x
    stops['y'] = stops['geometry'].y
    stops = stops[['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']]
    stops.to_csv(databaseFolder + 'bus_stop_wgs84.csv', index=False)


# if hour is larger than 24, convert it to the today's morning as 00:xx:xx
def StartTime(time):
    time_units = time.split(':')
    hours = int(time_units[0])
    hours = hours%24
    minutes = time_units[1]
    seconds = time_units[2]
    correct_hours ='foo'
    if hours == 0:
        correct_hours = '00'
    elif hours < 10:
        correct_hours = '0' + str(hours)
    else:
        correct_hours = str(hours)
    return ':'.join([correct_hours,minutes, seconds])

def EndTime(time):
    time_units = time.split(':')
    hours = int(time_units[0])
    if hours >= 24:
        return '23:59:59'
    minutes = time_units[1]
    seconds = time_units[2]
    correct_hours ='foo'
    if hours == 0:
        correct_hours = '00'
    elif hours < 10:
        correct_hours = '0' + str(hours)
    else:
        correct_hours = str(hours)
    return ':'.join([correct_hours,minutes, seconds])

def InSeconds(time):
    time_units = time.split(':')
    seconds = int(time_units[0])*3600 + int(time_units[1])*60 + int(time_units[2])
    seconds = seconds % (24 * 3600)
    return seconds


def timeFormat(seconds):
    if seconds >= 24*3600:
        return '23:59:59'
    else:
        h =  seconds // 3600 % 24
        m =  seconds // 60 % 60
        s =  seconds % 60
        units = [h, m, s]
        for i, u in enumerate(units):
            if u == 0:
                units[i] = '00'
            elif u < 10:
                units[i] = '0' + str(u)
            else:
                units[i] = str(u)
    return ':'.join(units)

def prepareBusDispatchFreq(headway=300):
    """
        pt_bus_dispatch_freq ['frequency_id', 'route_id', 'start_time', 'end_time', 'headway_sec']
        pt_bus_stops ['route_id', 'stop_code', 'sequence_no', 'trip_id']
        stoptime_df [trip_id, arrival_time, departure_time, stop_id, stop_sequence]
    Create frequency_time_table ['route_id', 'stop_code', 'sequence_no', 'arrival_time']
    """
    # all available time shape_id
    trips_gtfs = pd.read_csv(gtfsFolder + 'trips.txt')
    stoptime_gtfs = pd.read_csv(gtfsFolder + 'stop_times.txt')
    pt_bus_stops = pd.read_csv(processFolder + 'pre_pt_bus_stops.csv')
    stoptime_df = stoptime_gtfs.merge(trips_gtfs[['trip_id', 'shape_id']], on='trip_id', how='left')
    arrival = stoptime_df.groupby('shape_id')['arrival_time'].apply(list)
    arrival = arrival.apply(lambda times: [InSeconds(t) for t in times]).to_frame()

    arrival['start_time'] = arrival.apply(lambda r: min(r.arrival_time), axis=1)
    arrival['end_time'] = arrival.apply(lambda r: max(r.arrival_time), axis=1)
    arrival['shape_id'] = arrival.index

    pt_bus_stops.drop_duplicates(subset=['route_id'], inplace=True)
    dispatch_table = pt_bus_stops.merge(trips_gtfs[['trip_id', 'shape_id']], on='trip_id', how='left')
    dispatch_table= dispatch_table.merge(arrival[['shape_id', 'start_time', 'end_time']], on='shape_id', how='left')
    dispatch_table['headway_sec'] = headway
    dispatch_table['start_time'] = dispatch_table.apply(lambda r: timeFormat(r.start_time), axis=1)
    dispatch_table['end_time'] = dispatch_table.apply(lambda r: timeFormat(r.end_time), axis=1)
    print('num of unique route ids (start<final)', len(dispatch_table.route_id.unique()))

    assert(len(dispatch_table) == len(dispatch_table.route_id.unique()))
    FREQ_ID = dict(zip(dispatch_table.route_id, range(len(dispatch_table))))
    dispatch_table['frequency_id'] = dispatch_table.apply(lambda row: FREQ_ID[row.route_id], axis=1)

    dispatch_table = dispatch_table[['frequency_id', 'route_id', 'start_time', 'end_time', 'headway_sec']]
    dispatch_table.sort_values(by=['frequency_id'], inplace=True)
    dispatch_table.to_csv(databaseFolder + 'pt_bus_dispatch_freq.csv', index=False)


def findTravelTimeBetweenStops():
    stoptime_df = pd.read_csv(gtfsFolder  + 'stop_times.txt')
    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_stops.csv')
    stoptime_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)
    stoptime_df['stop_time_pair'] = stoptime_df.apply(lambda row: (row.stop_id, InSeconds(row.arrival_time)), axis=1)

    # Find travel time between consequent stops
    travelTime_btn_stops = {}
    for i, trip_stops in stoptime_df.groupby('trip_id'):
        for stop_times in zip(trip_stops.stop_time_pair[:-1], trip_stops.stop_time_pair[1:]):
            s1 = stop_times[0][0]
            s2 = stop_times[1][0]
            s1_time = stop_times[0][1]
            s2_time = stop_times[1][1]
            delta = s2_time - s1_time
            if delta > 0 and (not (s1, s2) in travelTime_btn_stops):
                travelTime_btn_stops[(s1, s2)] = delta

    # Computer estimate travel time for nonexisting time
    for i, routeDF in pt_bus_stops.groupby('route_id'):
        for stops in zip(routeDF.stop_code[:-1], routeDF.stop_code[1:]):
            if not stops in travelTime_btn_stops:
                print("TRAVEL TIME NEED TO BE SET for ", stops)
                #TODO: travelTime_btn_stops[stops] = DISTANCE / BUS_SPEED
                travelTime_btn_stops[stops] = 5 * 60 # 5 min default
    travelTime_btn_stops =  pd.DataFrame.from_records(list(travelTime_btn_stops.items()), columns=['stops', 'timeInSeconds'])
    travelTime_btn_stops.to_pickle(processFolder + 'travelTime_btn_stops.pkl')

def prepareJourneyTime():
    """
        pt_bus_dispatch_freq ['frequency_id', 'route_id', 'start_time', 'end_time', 'headway_sec']
        pt_bus_stops ['route_id', 'stop_code', 'sequence_no', 'trip_id']
        stoptime_df [trip_id, arrival_time, departure_time, stop_id, stop_sequence]
    Create frequency_time_table ['route_id', 'stop_code', 'sequence_no', 'arrival_time']
    """

    travelTime_btn_stops = pd.read_pickle(processFolder + 'travelTime_btn_stops.pkl')
    travelTime_btn_stops = dict(zip(travelTime_btn_stops.stops, travelTime_btn_stops.timeInSeconds))

    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_stops.csv')
    pt_bus_dispatch_freq = pd.read_csv(databaseFolder + 'pt_bus_dispatch_freq.csv')
    pt_bus_dispatch_freq['start_time_seconds'] = pt_bus_dispatch_freq.apply(lambda row: InSeconds(row.start_time), axis=1)
    startTime = dict(zip(pt_bus_dispatch_freq.route_id, pt_bus_dispatch_freq.start_time_seconds))

    print('pt_bus_stops ', pt_bus_stops.head(2))
    arrivalTime = {}
    for routeID, routeDF in pt_bus_stops.groupby('route_id'):
        arrival_time = int(startTime[routeID])
        arrivalTime[(routeID, 0)] = arrival_time
        for s1, s2, seq in zip(routeDF.stop_code[:-1], routeDF.stop_code[1:], routeDF.sequence_no[1:]):
            # print('stops --- ', s1, s2)
            arrival_time += int(travelTime_btn_stops[(s1, s2)])
            arrivalTime[(routeID, seq)] = arrival_time
    print('pt_bus_stops ', pt_bus_stops.columns)

    pt_bus_stops['arrival_time'] = pt_bus_stops.apply(lambda row: timeFormat(arrivalTime[(row.route_id, row.sequence_no)]), axis=1)
    pt_bus_stops.rename(columns={'sequence_no':'stop_sequence', 'route_id':'service_id', 'stop_code':'stop_id'}, inplace=True)
    NEW_TRIP_ID = dict(zip(pt_bus_stops.service_id.unique(), range(len(pt_bus_stops.service_id.unique()))))
    pt_bus_stops['trip_id'] = pt_bus_stops.apply(lambda row: NEW_TRIP_ID[row.service_id], axis=1)

    pt_bus_stops['departure_time'] = pt_bus_stops['arrival_time']
    pt_bus_stops['dwelling_time'] = '00:00:00'

    journey_table = pt_bus_stops[['service_id', 'trip_id', 'stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'dwelling_time']]
    journey_table.to_csv(databaseFolder + 'bus_journeytime_31Mar18.csv', index=False)

print('Preparing for ', simFolder)
# pruneShortTrips()
# createBusRouteTables()
# complete_bus_stops()
# prepareBusDispatchFreq()
# findTravelTimeBetweenStops()
# prepareJourneyTime()

# lat_long_stops()
# getRouteSegment()
