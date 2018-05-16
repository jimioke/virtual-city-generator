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
TELAVIV_CRS = {'init': 'epsg:2039'}

# Baltimore
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
    # ['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']
    segments = gpd.read_file(processFolder + 'SegmentGeo/SegmentGeo.shp')
    print('segments geo', segments.columns)
    segments.id = segments.id.astype(int)

    segments.index = segments.id
    segments['half_length'] = segments.apply(lambda row: row.geometry.length/2, axis=1)
    segments['seg_middle_point'] = segments.apply(lambda row: row.geometry.interpolate(0.5, normalized=True), axis=1)
    bus_stops_df = pd.read_csv(databaseFolder + 'pre_bus_stops.csv')
    bus_stops_df.id = bus_stops_df.id.astype(int)
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

def preparePreFreqTable():
    # pt_bus_stops_df = pd.DataFrame.from_records(pt_bus_stops_df, columns=['route_id', 'stop_code', 'sequence_no', 'shape_id' ])
    pt_bus_stops_df = pd.read_csv(processFolder + 'pre_pt_bus_stops.csv')
    trip_ids = pt_bus_stops_df.trip_id.unique()
    stoptime_df = pd.read_csv(gtfsFolder  + 'stop_times.txt')
    stoptime_df = stoptime_df[stoptime_df.trip_id.isin(trip_ids)]
    stoptime_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)
    pt_bus_stops_df = pt_bus_stops_df.merge(stoptime_df[['stop_id', 'trip_id', 'arrival_time']], left_on=['trip_id', 'stop_code'], right_on=['trip_id','stop_id'], how='left')
    print('All pt_bus_stops ', len(pt_bus_stops_df))
    pt_bus_stops_df.dropna(subset=['arrival_time'], inplace=True)
    print('Nan dropped All pt_bus_stops ', len(pt_bus_stops_df))
    pt_bus_stops_df.sort_values(by=['trip_id','sequence_no'], inplace=True)
    new_sequence = {}
    for trip_id, stops in pt_bus_stops_df.groupby('trip_id'):
        i = 0
        for indx, stop in stops.iterrows():
            new_sequence[(trip_id, stop.stop_id)] = i
            i +=1
    pt_bus_stops_df['sequence_no'] = pt_bus_stops_df.apply(lambda row: new_sequence[(row.trip_id, row.stop_id)], axis=1)

    pt_bus_stops_df.drop_duplicates(subset=['route_id','stop_code','sequence_no'], inplace=True)
    pt_bus_stops_df[['route_id', 'stop_code', 'sequence_no', 'arrival_time']].to_csv(processFolder + 'frequency_time_table.csv', index=False)
    pt_bus_stops_df[pt_bus_stops_cols].to_csv(databaseFolder + 'pt_bus_stops.csv', index=False)


def prepareFrequencyTables(headway=300):
    freq_table = pd.read_csv(processFolder + 'frequency_time_table.csv')
    freq_table.rename(columns={'sequence_no':'stop_sequence', 'stop_code':'stop_id'}, inplace=True)
    print('frequency_time_table ', freq_table.columns)
    freq_table['original_time'] = freq_table['arrival_time']
    print('freq_table-----------')
    freq_table['arrival_in_sec'] = freq_table.apply(lambda row: InSeconds(row.arrival_time), axis=1)
    freq_table['arrival_time'] = freq_table.apply(lambda row: timeFormat(row.arrival_in_sec), axis=1)
    freq_table['departure_in_sec'] = freq_table['arrival_in_sec']
    freq_table['departure_time'] = freq_table['arrival_time']
    freq_table['headway_sec'] = headway
    freq_table['dwelling_time'] = '00:00:00'

    # Give an unique frequency id (we drop duplicates)
    routes = freq_table['route_id'].unique()
    FREQ_ID = dict(zip(routes, range(len(routes))))
    freq_table['frequency_id'] = freq_table.apply(lambda row: FREQ_ID[row.route_id], axis=1)

    # SimMobility bus frequency table (trip start to end specific)
    dispatch_table = freq_table.rename(columns={'arrival_time':'start_time', 'departure_time':'end_time'})
    dispatch_table.sort_values(by=['route_id', 'arrival_in_sec'], inplace=True) #'stop_sequence'
    start_dispatch = dispatch_table.drop_duplicates(subset=['route_id'], keep='first')
    end_dispatch = dispatch_table.drop_duplicates(subset=['route_id'], keep='last')
    dispatch_table_final = start_dispatch[['frequency_id', 'route_id', 'start_time', 'headway_sec', 'arrival_in_sec']].merge(end_dispatch[['route_id', 'end_time', 'departure_in_sec']], on='route_id', how='left')
    print('num of rows dispatch_table_final ', len(dispatch_table_final))
    print('num of unique route ids ', len(dispatch_table_final.route_id.unique()))
    dispatch_table_final = dispatch_table_final[dispatch_table_final.arrival_in_sec < dispatch_table_final.departure_in_sec]
    dispatch_table_final = dispatch_table_final[dispatch_table_final.start_time != dispatch_table_final.end_time]
    print('num of unique route ids (start<final)', len(dispatch_table_final.route_id.unique()))
    dispatch_table_final = dispatch_table_final[['frequency_id', 'route_id', 'start_time', 'end_time', 'headway_sec']]
    dispatch_table_final.sort_values(by=['frequency_id'], inplace=True)
    dispatch_table_final.to_csv(databaseFolder + 'pt_bus_dispatch_freq.csv', index=False)

    # Public transit graph frequency table (stop to stop specific)
    journey_table = freq_table.rename(columns={'route_id': 'service_id', 'frequency_id':'trip_id'})
    journey_table.drop_duplicates(subset=['service_id', 'stop_sequence'], keep='first', inplace=True)
    journey_table['departure_time'] = journey_table['arrival_time'] # convention for public transit graph generation intput.
    journey_table = journey_table[['service_id', 'trip_id', 'stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'dwelling_time']]
    journey_table.to_csv(databaseFolder + 'bus_journeytime_31Mar18.csv', index=False)
    print('Number of services ', len(journey_table.service_id.unique()))

print('Preparing for ', simFolder)
# pruneShortTrips()
# createBusRouteTables()
# complete_bus_stops()
# preparePreFreqTable()
prepareFrequencyTables()
# lat_long_stops()
# getRouteSegment()
