import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import Point
from shapely.geometry import MultiPoint
import math
from collections import defaultdict
# from ast import literal_eval
import datetime

LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}

# PREPARE SIMMOBILITY
# simFolder = 'Auto_sprawl_drive_main/simmobility/'
# gtfsFolder = 'clean-gtfs/MergedBus/'
# processFolder = 'process_big/'
# databaseFolder = 'to_db_big/'

# Small example
simFolder = 'Baltimore_small/simmobility/'
gtfsFolder = 'gtfs_source_small_example/gtfs-QueenAnne/'
processFolder = 'process_small_example/'
databaseFolder = 'to_db/'

# SimMobility table headers
bus_stops_cols = ['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']
pt_bus_stops_cols = ['route_id', 'stop_code', 'sequence_no']
pt_bus_routes_cols = ['route_id', 'sequence_no', 'section_id']
frequence_cols = ['frequency_id', 'line_id', 'start_time', 'end_time', 'headway_sec']
journey_cols = ['service_id', 'trip_id', 'stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'dwelling_time']


def getSubtripMetrics():
    connectedTrips = pd.read_pickle(processFolder + 'subtrips_wSegments.pkl')
    connectedTrips['len_stops'] = connectedTrips.apply(lambda row: len(row.stops), axis=1)
    connectedTrips['len_uniq_stops'] = connectedTrips.apply(lambda row: len(set(row.stops)), axis=1)
    print('Number of the same segment consequent stops')
    print(len(connectedTrips[connectedTrips.len_stops != connectedTrips.len_uniq_stops]))
    connectedTrips['len_path_in_seg'] = connectedTrips.apply(lambda row: len(row.path_segments), axis=1)
    print("stops ---------------")
    print(connectedTrips.len_stops.value_counts())
    # print("paths ----------------")
    print(connectedTrips.len_stops.sum())
    # print(connectedTrips.len_path_in_seg.value_counts())


# Prune out bus stop sequences so that bus
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

# cleanSubtrips()

# Create pt_bus_routes and pt_bus_stops and pre prepare bus_stops.
def createBusRouteTables():
    # [['trip_id', 'shape_id', 'stop_segments', 'path_segments', 'stops']]
    # connectedTrips = pd.read_pickle(processFolder + 'subtrips_wSegments.pkl')
    connectedTrips = pruneShortTrips()
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
            pt_bus_stops_df.append( (trip.route_id, i_stop, i))
        for i, seg in enumerate(trip.path_segments):
            pt_bus_routes_df.append( (trip.route_id, i, seg))

    pt_bus_stops_df = pd.DataFrame.from_records(pt_bus_stops_df, columns=['route_id', 'stop_code', 'sequence_no' ])
    pt_bus_routes_df = pd.DataFrame.from_records(pt_bus_routes_df, columns=['route_id', 'sequence_no', 'section_id'])
    bus_stops_df = pd.DataFrame.from_records(bus_stops_df, columns=['id', 'section_id'])
    bus_stops_df['terminal'] = bus_stops_df.apply(lambda row: int(row.id in terminal_stops), axis=1)

    pt_bus_stops_df.to_csv(databaseFolder + 'pt_bus_stops.csv', index=False)
    pt_bus_routes_df.to_csv(databaseFolder + 'pt_bus_routes.csv', index=False)
    bus_stops_df.to_csv(databaseFolder + 'pre_bus_stops.csv', index=False)
    connectedTrips.to_pickle(processFolder + 'unique_subtrips_wSegments.pkl')


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
# ['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']
    segments = gpd.read_file(processFolder + 'SegmentGeo/SegmentGeo.shp')
    print('segments geo', segments.columns)
    segments.index = segments.id
    segments['half_length'] = segments.apply(lambda row: row.geometry.length/2, axis=1)
    segments['seg_middle_point'] = segments.apply(lambda row: row.geometry.interpolate(0.5, normalized=True), axis=1)
    # print(segments.head(2))
    bus_stops_df = pd.read_csv(databaseFolder + 'pre_bus_stops.csv')
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

    print(bus_stops_df[bus_stops_df.section_offset != 0].head(3))
    # bus_stops_df_duplicated = bus_stops_df[bus_stops_df.duplicated(['id'], keep=False)]
    # bus_stops_df_duplicated.to_csv(databaseFolder + 'bus_stop_duplicated.csv', index=False)
    # print(bus_stops_df_duplicated.head(10))
    print('Number of unique stops ', len(bus_stops_df.id.unique()))
    print('Number of stops ', len(bus_stops_df))
    # Number of unique stops  3472
    # Number of stops  3472

def lat_long_stops():
    stops = pd.read_csv(databaseFolder + 'bus_stop.csv')
    coords = [Point(xy) for xy in zip(stops.x, stops.y)]
    stops = gpd.GeoDataFrame(stops, crs=BALTIMORE_CRS, geometry=coords)
    stops = stops.to_crs(LAT_LONG_CRS)
    stops['x'] = stops['geometry'].x
    stops['y'] = stops['geometry'].y
    stops = stops[['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']]
    stops.to_csv(databaseFolder + 'bus_stop_wgs84.csv', index=False)

# lat_long_stops()

def sublist_index(large_l, small_l):
    if len(large_l) < len(small_l):
        return None
    subset_index = []
    index = 0
    for i in small_l:
        while index < len(large_l) and large_l[index] != i:
            index += 1
        if index >= len(large_l):
            return None
        subset_index.append(index)
    return subset_index
# Test sublist_index
# print(sublist_index([0,1,2,3,4,5,6], [3,6]))
# print(sublist_index([0,1,2,3,4,5,6], [3,6,7]))
# print(sublist_index([0,1,2,3,4,5,6], [0, 3,6]))
# print(sublist_index([0,1,2,3,4,5,6], [0, 3,4]))

def preparePreFreqTable():
    # [['trip_id', 'shape_id', 'stop_segments', 'path_segments', 'stops', route_id]]
    subtrips = pd.read_pickle(processFolder + 'unique_subtrips_wSegments.pkl')
    # ['route_id', 'stop_code', 'sequence_no' ]
    trip_df = pd.read_csv(gtfsFolder  + 'trips.txt')
    stoptime_df = pd.read_csv(gtfsFolder  + 'stop_times.txt')
    stoptime_df = stoptime_df.merge(trip_df[['trip_id', 'shape_id']], on='trip_id', how='left')
    stoptime_df = stoptime_df[stoptime_df.shape_id.isin(subtrips.shape_id.unique())]

    frequency_df = [] # route, stops, stoptimes
    for trip_id, trip_stoptime in stoptime_df.groupby('trip_id'):
        trip_stops = trip_stoptime.stop_id.values
        trip_stoptimes = trip_stoptime.arrival_time.values
        trip_shape_id = trip_stoptime.shape_id.values[0]
        routes_shape = subtrips[subtrips.shape_id == trip_shape_id]
        for indx, route in routes_shape.iterrows():
            # If this subtrip is in this stoptime
            subset_index = sublist_index(trip_stops, route.stops)
            if subset_index:
                route_stoptimes = [trip_stoptimes[i] for i in subset_index]
                frequency_df.append((route.route_id, trip_id, route.stops, route_stoptimes))

    frequency_df = pd.DataFrame.from_records(frequency_df, columns=['route_id', 'trip_id', 'stops', 'stoptimes'])
    freq_table = []

    for indx, row in frequency_df.iterrows():
        for i in range(len(row.stops)):
            freq = (row.route_id, row.stops[i], row.stoptimes[i], i)
            freq_table.append(freq)

    freq_table = pd.DataFrame.from_records(freq_table, columns=['route_id', 'stop_id', 'arrival_time', 'stop_sequence'])
    freq_table.to_csv(processFolder + 'frequency_time_table.csv')
    print('Number of unique routes ', len(freq_table.route_id.unique()))
    # Number of unique frequencies  409534
    # Number of unique routes  425
    # After cleaning
    # Number of unique frequencies  369563
    # Number of unique routes  627
    # num of rows1  627
    # num of rows2  626 626

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
    return seconds


def timeFormat(seconds):
    if seconds >= 24*3600:
        return '23:59:59'
    else:
        h =  seconds // 3600 %24
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

def prepareFrequencyTables(headway=300):
    freq_table = pd.read_csv(processFolder + 'frequency_time_table.csv')
    freq_table['original_time'] = freq_table['arrival_time']
    freq_table['arrival_in_sec'] = freq_table.apply(lambda row: InSeconds(row.arrival_time), axis=1)
    freq_table['departure_in_sec'] = freq_table.apply(lambda row: InSeconds(row.arrival_time), axis=1) # for later

    freq_table['arrival_time'] = freq_table.apply(lambda row: timeFormat(row.arrival_in_sec), axis=1)
    freq_table['departure_time'] = freq_table.apply(lambda row: timeFormat(row.arrival_in_sec), axis=1)
    freq_table['headway_sec'] = headway
    freq_table['dwelling_time'] = '00:00:00'

    # Give an unique frequency id (we drop duplicates)
    routes = freq_table['route_id'].unique()
    FREQ_ID = dict(zip(routes, range(len(routes))))
    freq_table['frequency_id'] = freq_table.apply(lambda row: FREQ_ID[row.route_id], axis=1)

    # SimMobility bus frequency table (trip start to end specific)
    dispatch_table = freq_table.rename(columns={'route_id':'line_id', 'arrival_time':'start_time', 'departure_time':'end_time'})
    dispatch_table.sort_values(by=['line_id', 'arrival_in_sec'], inplace=True) #'stop_sequence'
    start_dispatch = dispatch_table.drop_duplicates(subset=['line_id'], keep='first')
    end_dispatch = dispatch_table.drop_duplicates(subset=['line_id'], keep='last')
    dispatch_table_final = start_dispatch[['frequency_id', 'line_id', 'start_time', 'headway_sec','arrival_in_sec', 'original_time']].merge(end_dispatch[['line_id', 'end_time', 'departure_in_sec', 'original_time']], on='line_id', how='left')
    print('num of rows1 ', len(dispatch_table_final))
    dispatch_table_final = dispatch_table_final[dispatch_table_final.arrival_in_sec < dispatch_table_final.departure_in_sec]
    print('num of rows2 ', len(dispatch_table_final), len(dispatch_table_final.line_id.unique()))
    dispatch_table_final = dispatch_table_final[['frequency_id', 'line_id', 'start_time', 'end_time', 'headway_sec']]
    dispatch_table_final.to_csv(databaseFolder + 'pt_bus_dispatch_freq.csv', index=False)

    # Public transit graph frequency table (stop to stop specific)
    journey_table = freq_table.rename(columns={'route_id': 'service_id', 'frequency_id':'trip_id'})
    journey_table.drop_duplicates(subset=['service_id', 'stop_sequence'], keep='first', inplace=True)
# ourney_table.service_id.unique()
    journey_table['departure_time'] = journey_table['arrival_time'] # convention for public transit graph generation intput.
    # journey_table['trip_id'] = 0
    journey_table = journey_table[['service_id', 'trip_id', 'stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'dwelling_time']]
    journey_table.to_csv(databaseFolder + 'bus_journeytime_31Mar18.csv', index=False)
    print('Number of servies ', len(journey_table.service_id.unique()))


# pruneShortTrips()
createBusRouteTables()
complete_bus_stops()
preparePreFreqTable()
prepareFrequencyTables()
