################################################################################
# Description: helper functions for creating SimMobility tables.
# Written by: Iveel Tsogsuren
################################################################################
import pandas as pd
import geopandas as gpd
import datetime
from collections import defaultdict, namedtuple
from shapely.geometry import Point, LineString, MultiPoint, MultiLineString, mapping, Polygon
from shapely.ops import transform, split, nearest_points
import fiona
from functools import partial
import pyproj
import numpy as np


LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}
CURRENT_CRS = BALTIMORE_CRS

WEEKDAY_SERVICES = ['1']
HEADWAY_SEC = 60

DEFAULT_SPEED_LIMIT = 70
ACCELERATE_RATE = 1.1
DECELERATE_RATE = 1.1
Route_type = namedtuple('Route_type', 'type_name type_int platform_length capacity')
ROUTE_TYPE = {
0: Route_type(type_name='LR', type_int=0, platform_length=56, capacity=105),
1: Route_type(type_name='CR', type_int=1, platform_length=60, capacity=170),
2: Route_type(type_name='HR', type_int=1, platform_length=142, capacity=1920),
}

# 0 - Tram, Light Rail, Streetcar - 900
# 1 - Subway, Metro - 400
# 2 - Rail - 100
# 3 - Bus - 700
# 4 - Ferry - 1000
# 5 - Cable Car - ?
# 6 - Gondola, Suspended cable car - 1300
# 7 - Funicular - 1400

def convertCoordinates(toCRS=CURRENT_CRS):
    """ Convert train stops crs from xy to lat and long. """
    inputFolder = 'Outputs/to_db/'
    stops = pd.read_csv(inputFolder + 'mrt_stop.csv')
    stops_cols = stops.columns
    coords = [Point(xy) for xy in zip(stops.x, stops.y)]
    stops = gpd.GeoDataFrame(stops, crs=toCRS, geometry=coords)
    stops = stops.to_crs(LAT_LONG_CRS)
    stops['x'] = stops['geometry'].x
    stops['y'] = stops['geometry'].y
    stops = stops[stops_cols]
    stops.to_csv(inputFolder + 'mrt_stop_wgs84.csv', index=False)


def get_gtfs(inFolder='Merged_clean/'):
    """ Read GTFS files into panda dataFrames. """
    route = pd.read_csv(inFolder + 'route.csv')
    shape = pd.read_csv(inFolder + 'shapes.csv')
    stops = pd.read_csv(inFolder + 'stops.csv')
    stoptime = pd.read_csv(inFolder + 'stop_times.csv')
    trip = pd.read_csv(inFolder + 'trips.csv')
    # Set shape_id as numbers
    # shape_ids = shape.shape_id.unique()
    # shapeIDmap = dict(zip(shape_ids, ['L' + str(i) for i in range(1, len(shape_ids)+1)]))
    # shape['shape_id'] = shape.apply(lambda row: shapeIDmap[row.shape_id], axis=1)
    # trip['shape_id'] = trip.apply(lambda row: shapeIDmap[row.shape_id], axis=1)
    return route, shape, stops, stoptime, trip

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def createLinesPlatformName(stoptime_df, stops_df, trip_df, route, shape, LineInfo):
    """
    Route and shape_id(s) are consistent in input files at this point.
    Map trips to lines based on trip shapes.
    Extend stoptime by line_id and shape_id
    For each shape, find all trips and choose a representive trip.

    Parameters
    ----------
    stoptime_df, stops_df, trip_df, route, shape : standard GTFS files in pandas dataFrames.
    LineInfo : Specification for which an opposite pair of shapes each route has.

    Returns
    -------
    stoptime_df : added extra columns line_id, direction, shape_id, etc.
    trip : lines' only representive trips
    linetime : only representive trips' stoptime
    line_toStartTimes : line's start times of all trips
    """
    # keep a representive trip (stop sequence) for each shape.
    # We will assume that other trips with the same line_id have the same stop sequences.
    trip = trip_df.copy()
    trip['direction'] = trip.apply(lambda row: LineInfo[row.shape_id].direction, axis=1)
    trip['generic_line'] = trip.apply(lambda row: LineInfo[row.shape_id].line, axis=1)
    trip['line_id'] = trip.apply(lambda row: row.generic_line + '_' + str(row.direction), axis=1)
    trip['opp_line'] = trip.apply(lambda row: row.generic_line + '_' + str(LineInfo[row.shape_id].opp_direction), axis=1)

    stoptime_df = stoptime_df.merge(trip[['trip_id', 'line_id', 'opp_line', 'route_id', 'shape_id', 'service_id', 'generic_line', 'direction']], on='trip_id', how='left')
    # Choose a representive trip for each shape.
    repTrips = trip_df.groupby('shape_id')['trip_id'].apply(lambda row: list(row)[0])
    trip = trip_df[trip_df.trip_id.isin(repTrips.values)]
    line_toStartTimes = stoptime_df[stoptime_df.stop_sequence == 1].groupby('line_id')['arrival_time'].apply(set)

    linetime = stoptime_df[stoptime_df.trip_id.isin(repTrips.values)]
    linetime = linetime.merge(stops_df, on='stop_id', how='left')
    linetime = linetime.merge(route[['route_id', 'route_type']], on='route_id', how='left')
    linetime = linetime[linetime.service_id.isin(WEEKDAY_SERVICES)]

    linetime.sort_values(by=['trip_id', 'stop_sequence'], inplace=True) # get a unique trip
    linetime['type'] = linetime.apply(lambda row: ROUTE_TYPE[row.route_type].type_name, axis=1)
    linetime['type_int'] = linetime.apply(lambda row: ROUTE_TYPE[row.route_type].type_int, axis=1)
    linetime['capacity'] = linetime.apply(lambda row: ROUTE_TYPE[row.route_type].capacity, axis=1)
    linetime['length'] = linetime.apply(lambda row: ROUTE_TYPE[row.route_type].platform_length, axis=1)
    # Name platforms. Stops in different lines have different platfrom names.
    def setPlatformNo(row, df):
        if row.direction == 1:
            return row.generic_line + str(row.stop_sequence) + '_' + str(row.direction)
        else:
            num_stops = df[df.line_id == row.line_id].stop_sequence.max()
            return row.generic_line + str(num_stops + 1 - row.stop_sequence) + '_' + str(row.direction)

    linetime['platform_no'] = linetime.apply(lambda row: setPlatformNo(row, linetime), axis=1)
    # print(linetime[['stop_sequence', 'line_id', 'opp_line', 'platform_no']])
    print('Number of stops in lines', len(linetime.stop_id.unique()))
    print('Number of trips in lines', len(linetime.trip_id.unique()))
    return trip, stoptime_df, linetime, line_toStartTimes


def platform_stations(linetime, stops):
    """
    Construct train stations. Train platforms are allocated to the single train
    station if they are at the same location.
    Parameters
    ----------
    linetime : representive trips' stoptime
    stops : a standard stops GTFS (cleaned such that oppostie directional two
                                    stops are the same location)
    Returns
    -------
    train_stop : SimMobility train_stop table (unique station_no). This table is
                used for public transit graph generation and has a different
                naming convention.
    train_platform : SimMobility train_platform table (all platforms).
    line_stoptime : added station_no column.
    """
    # Find stations
    coords_to_lines = defaultdict(list)
    coords_to_platforms = defaultdict(list)
    # Find platforms (without direction) of lines which share the same stop coordinates.
    # These platform share the same station.
    for indx, row in linetime.iterrows():
        # Check if there is already representive stop from line
        if row.generic_line not in coords_to_lines[(row.stop_lon, row.stop_lat)]:
            coords_to_lines[(row.stop_lon, row.stop_lat)].append(row.generic_line)
            coords_to_platforms[(row.stop_lon, row.stop_lat)].append(row.platform_no.split('_')[0]) # row.generic_line))
    print('###### Number of stations ', len(coords_to_lines))
    coords_to_stationName = {}
    for coords, line_list in coords_to_platforms.items():
        coords_to_stationName[coords] = '/'.join(sorted(set(line_list)))
    print('platform and station coords_to_platforms')
    print(coords_to_platforms)
    print('platform and station coords_to_stationName')
    print(coords_to_stationName)
    print('platform and station coords_to_lines')
    print(coords_to_lines)

    linetime['station_no'] = linetime.apply(lambda row: coords_to_stationName[(row.stop_lon, row.stop_lat)], axis=1)
    # Create train_stop table (Be careful with absurd name convention)
    train_stop = linetime.drop_duplicates(subset=['station_no'])
    train_stop.rename(columns={'stop_y':'y', 'stop_x':'x', 'station_no':'platform_name', 'stop_name':'station_name'}, inplace=True)
    train_stop['shape_id'] = train_stop.reset_index().index + 1
    train_stop['id'] = train_stop['shape_id']
    train_stop['op_year'] = 1997
    train_stop['z'] = 0
    train_stop = train_stop[['shape_id', 'x', 'y', 'z', 'id', 'platform_name', 'station_name', 'type', 'op_year']]

    # Create train_platform table
    train_platform = linetime.copy()
    train_platform['pos_offset'] = 0
    train_platform.rename(columns={'type': 'string_type', 'type_int':'type'}, inplace=True)
    train_platform = train_platform[['platform_no', 'station_no', 'line_id', 'capacity', 'type', 'block_id', 'pos_offset', 'length']]
    print('Number of stations in platform table', len(train_platform.station_no.unique()))
    print('Number of platforms in platform table', len(train_platform.platform_no.unique()))
    # print(linetime)
    return train_stop, train_platform, linetime

def convertSegment(simFolder=None, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS):
    segment_points = pd.read_csv(simFolder + 'segment-nodes.csv')
    pointGeo = [Point(xy) for xy in zip(segment_points.x, segment_points.y)]
    segment_points = gpd.GeoDataFrame(segment_points, crs=fromCRS, geometry=pointGeo)
    segment_points = segment_points.to_crs(toCRS)
    segment_points['x'] = segment_points['geometry'].x
    segment_points['y'] = segment_points['geometry'].y
    segment_points['coords'] = segment_points.apply(lambda row: (row.x, row.y), axis=1)
    segment_points = segment_points[['id', 'x', 'y', 'coords']]
    segment_points.to_csv(simFolder + 'segment-baltimore-crs.csv')

def find_access_segment(train_stop, simFolder=None, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS):
    segment_points = pd.read_csv(simFolder + 'segment-baltimore-crs.csv')
    segment_points['coords'] = segment_points.apply(lambda row: (row.x, row.y), axis=1)
    points = MultiPoint(segment_points.coords.tolist())
    print('unique stops ', len(train_stop))
    access_segment = []
    for indx, row in train_stop.iterrows():
        nearest = nearest_points(points, Point(row.x, row.y))[0]
        access_segment.append(((nearest.x, nearest.y), row.shape_id))
    access_segment = pd.DataFrame.from_records(access_segment, columns = ['nearest_coord', 'mrt_stop_id'])
    access_segment = access_segment.merge(segment_points, left_on='nearest_coord', right_on='coords', how='left')
    access_segment = access_segment[['mrt_stop_id', 'id']].rename(columns={'id':'segment_id'})
    access_segment.drop_duplicates(subset=['mrt_stop_id'], inplace=True)
    return access_segment

def constructSeqLine(df, idColumn='id', seqColumn='seq_id', x='x', y='y'):
    df = df.sort_values([seqColumn])
    grouped = df.groupby(idColumn)
    rows = []
    for name,group in grouped:
        line_coords = group[[x, y]]
        line = LineString(tuple(x) for x in line_coords.to_records(index=False))
        rows.append( (name, line) )
    return pd.DataFrame.from_records(rows, columns=[idColumn, 'geometry'])

def addRouteGeo(stops_df, shapes_df, fromCRS=LAT_LONG_CRS, toCRS=CURRENT_CRS):
    # print('stops ', stops.columns)
    # print('shapes ', shapes.columns)
    stopGeo = [Point(xy) for xy in zip(stops_df.stop_lon, stops_df.stop_lat)]
    # print('stopGeo ', stopGeo)
    stops = gpd.GeoDataFrame(stops_df, crs=fromCRS, geometry=stopGeo)
    stops = stops.to_crs(toCRS)
    shapeGeo = constructSeqLine(shapes_df, idColumn= 'shape_id', seqColumn='shape_pt_sequence', x='shape_pt_lon', y='shape_pt_lat')
    shapeGeo = gpd.GeoDataFrame(shapeGeo, crs=fromCRS)
    shapeGeo = shapeGeo.to_crs(toCRS)
    return stops, shapeGeo


def write(a_shape, shape_type, toFile):
    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': shape_type,
        'properties': {'id': 'int'},
    }

    # Write a new Shapefile
    with fiona.open(toFile, 'w', 'ESRI Shapefile', schema) as c:
        ## If there are multiple geometries, put the "for" loop here
        c.write({
            'geometry': mapping(a_shape),
            'properties': {'id': 123},
        })

def createBlocks(stoptime, shape):
    """
    Project stops onto the corresponding shapes
    Split shapes into blocks such that each stop is a middle or
    end point (for two ends) of a block.
    Index (ID) blocks and their polylines -> train_block, block_polyline
    Express routes in stop sequence and block sequence -> train_route_platform, train_route
    Express each stop sequence by a block sequence -> train_route
    stoptime

    Parameters
    ----------
    stoptime : representive trips' stoptimes
    shape : a standard GTFS shape

    Returns
    -------
    train_route_platform : route expressed in a stop (platform) sequence
    train_route : route expressed in a block sequence
    train_block : blocks
    block_polyline : block polylines
    stoptime : added by block_id based on stop_id
    """
    stoptime, shape = addRouteGeo(stoptime, shape)
    stoptime.sort_values(by=['line_id', 'stop_sequence'], inplace=True)
    stoptime['x'] = stoptime.geometry.x
    stoptime['y'] = stoptime.geometry.y
    shape.index = shape.shape_id

    def neartestPoint(row, shapes_df):
        # print('row ', row)
        line = MultiPoint(shapes_df.at[row.shape_id, 'geometry'].coords)
        point = row.geometry
        projected_point = nearest_points(line, point)
        return (projected_point[0].x, projected_point[0].y) # make a tuple
    stoptime['proj_on_line'] = stoptime.apply(lambda row: neartestPoint(row, shape), axis=1)

    shape_stops = stoptime.groupby('shape_id')['proj_on_line'].apply(list).to_frame().reset_index()
    shape_stops.index = shape_stops.shape_id

    shape_to_blocks = {}
    for shape_id, row in shape_stops.iterrows():
        proj_stops = row['proj_on_line']
        if len(proj_stops) > 2 and len(set(proj_stops)) == len(proj_stops):
            proj_stops_cutter = MultiPoint(proj_stops[1:-1]) # exclude end stops
            line = shape.at[shape_id, 'geometry']
            splitted = split(line, proj_stops_cutter)
            splitted_lines = MultiLineString(splitted)
            # Cut into blocks
            cutter_points = [s.interpolate(0.5, normalized=True) for s in splitted]
            lineMultipoint = MultiPoint(line.coords)
            cut_on = MultiPoint([nearest_points(lineMultipoint, P)[0] for P in cutter_points])
            line_blocks = split(line, cut_on)
            if len(proj_stops) == len(line_blocks):
                shape_to_blocks[shape_id] = list(line_blocks)

    # Create block related tables
    print('Number of lines splitted into blocks ', len(shape_to_blocks))
    shape_stops = shape_stops[shape_stops.shape_id.isin(shape_to_blocks.keys())]
    shape_stopseq = stoptime[stoptime.shape_id.isin(shape_to_blocks.keys())]

    shape_stopseq = shape_stopseq.groupby('shape_id')['platform_no'].apply(list)
    shape_stopseq = shape_stopseq.to_frame().reset_index()
    shape_stopseq.index = shape_stopseq.shape_id
    platform_to_block = {}
    train_route_platform = []
    BLOCK_ID = 1
    block_to_poly = {}
    for shape_id, row in shape_stopseq.iterrows():
        sequence_no = 0
        for index, platform in enumerate(row.platform_no):
            stop_b = (shape_id, platform, sequence_no)
            platform_to_block[platform] = BLOCK_ID
            # print(len(shape_to_blocks[line_id]), len(row.platform_no))
            # print(shape_to_blocks[line_id])
            block_to_poly[BLOCK_ID] = shape_to_blocks[shape_id][index]
            train_route_platform.append(stop_b)
            BLOCK_ID += 1
            sequence_no +=1

    train_route_platform = pd.DataFrame.from_records(train_route_platform, columns=['shape_id', 'platform_no', 'sequence_no'])
    print('train_route_platform ', train_route_platform.head(10))
    train_route_platform = train_route_platform.merge(stoptime[['shape_id', 'line_id']], on='shape_id', how='left')
    train_route_platform = train_route_platform.drop_duplicates(subset=['line_id','platform_no'])
    train_route = train_route_platform.copy()
    train_route['block_id'] = train_route.apply(lambda row: platform_to_block[row.platform_no], axis=1)
    stoptime['block_id'] = stoptime.apply(lambda row: platform_to_block[row.platform_no], axis=1)
    train_route = train_route[['line_id', 'block_id', 'sequence_no']]

    # Create blocks
    block_polyline = []
    train_block = []
    for blockID, lineString in block_to_poly.items():
        train_block.append((blockID, lineString.length))
        for indx, coord in enumerate(list(lineString.coords), 1):
            poly = (blockID, coord[0], coord[1], 0, indx)
            block_polyline.append(poly)

    train_block = pd.DataFrame.from_records(train_block, columns=['block_id', 'length'])
    block_polyline = pd.DataFrame.from_records(block_polyline, columns=['polyline_id', 'x', 'y', 'z', 'sequence_no'])
    train_block['default_speed_limit'] = DEFAULT_SPEED_LIMIT
    train_block['accelerate_rate'] = ACCELERATE_RATE
    train_block['decelerate_rate'] = DECELERATE_RATE
    print('Number of platforms ', len(train_route_platform.platform_no.unique()))
    print('Number of blocks ', len(train_block.block_id.unique()))
    print('Number of lines ', len(train_route.line_id.unique()))
    return train_route_platform, train_route, train_block, block_polyline, stoptime


# if a train starts before midnight but ends after midnight, we drop this
def overMidnight(row):
    # if row.start
    time_units = time.split(':')
    if int(time_units[0]) >=24:
        return True
    return False

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
    # time = row["Start_Time"]
    start_time = datetime.datetime.strptime(time, "%H:%M:%S")
    end_time = start_time + datetime.timedelta(minutes=1)
    return end_time.strftime("%H:%M:%S")

def dispatch_freq(line_stoptime, stoptime, line_toStartTimes):
    # print(line_stoptime.columns)
    # print(stoptime.columns)
    # stoptime.rename(columns={'arrival_time':'original_arrival_time'}, inplace=True)
    stoptime = pd.merge(stoptime[['arrival_time', 'shape_id', 'stop_sequence', 'trip_id']],
                        line_stoptime[['shape_id', 'stop_sequence', 'station_no', 'type', 'stop_lon', 'stop_lat', 'line_id']],
                        on=['shape_id', 'stop_sequence'], how='left')
    # print(stoptime)
    stoptime['start_time'] = stoptime.apply(lambda row: StartTime(row.arrival_time), axis=1)
    stoptime['end_time'] = stoptime['start_time']
    stoptime['headway_sec'] = HEADWAY_SEC

    dispatch_start = stoptime.sort_values(by=['trip_id', 'stop_sequence']).drop_duplicates(subset=['trip_id'], keep='first')
    dispatch_end = stoptime.sort_values(by=['trip_id', 'stop_sequence'], ascending=[True, False]).drop_duplicates(subset=['trip_id'], keep='first')
    dispatch = pd.merge(dispatch_start[['trip_id', 'line_id', 'headway_sec', 'start_time']],
                                   dispatch_end[['trip_id', 'end_time']], on='trip_id', how='left')

    # Remove overnight trips
    dispatch = dispatch[dispatch.start_time < dispatch.end_time]
    valied_trips = dispatch.trip_id.unique()

    dispatch.rename(columns={'trip_id':'frequency_id'}, inplace=True)
    dispatch = dispatch[['frequency_id', 'line_id', 'start_time', 'end_time', 'headway_sec']]
    # print('stoptime', stoptime.columns)

    dispatch_detialed = stoptime.rename(columns={'start_time':'arrival_time', 'arrival_time':'arrival_time_old', 'end_time':'departure_time',
            'station_no':'stop_id','type':'C_type', 'stop_lon':'stop_long', 'service_id':'service_id_gtfs', 'line_id':'service_id'})
    # Remove overnight trips
    dispatch_detialed = dispatch_detialed[dispatch_detialed.trip_id.isin(valied_trips)]
    dispatch_detialed['service'] =  dispatch_detialed['service_id']
    # dispatch_detialed = dispatch_detialed[]
    dispatch_detialed.sort_values(by=['service_id', 'trip_id', 'stop_sequence'], inplace=True)
    print('number of frequencey ', len(dispatch.frequency_id.unique()))
    print('number of lines ', len(dispatch.line_id.unique()))
    return dispatch, dispatch_detialed


def transfer_time(platforms):
    train_platform = ['platform_no', 'station_no', 'line_id', 'capacity', 'type', 'block_id', 'pos_offset', 'length']
    pt_train_platform_transfer_time = ['station_no', 'platform_first', 'platform_second', 'transfered_time_sec']
    transfer_time = []
    for station, platforms in platforms.groupby('station_no'):
        # print(type(platforms))
        # return
        for i1, p1 in platforms.iterrows():
            for i2, p2 in platforms.iterrows():
                if p1.platform_no != p2.platform_no:
                    if p1.platform_no.split('_')[0] == p2.platform_no.split('_')[0]:
                        t1 = (station, p1.platform_no, p2.platform_no, 0)
                        t2 = (station, p2.platform_no, p1.platform_no, 0)
                    else:
                        t1 = (station, p1.platform_no, p2.platform_no, 60)
                        t2 = (station, p2.platform_no, p1.platform_no, 60)
                    transfer_time += [t1, t2]
    transfer_time = pd.DataFrame.from_records(transfer_time, columns = ['station_no', 'platform_first', 'platform_second', 'transfered_time_sec'])
    transfer_time.drop_duplicates(subset=['station_no', 'platform_first', 'platform_second'], inplace=True)
    return transfer_time


def create_uturn(pt_train_route, pt_train_platform):
    # Step 18: Create train_uturn_platforms table
    pt_train_route_copy = pt_train_route.copy()
    pt_train_platform_copy = pt_train_platform.copy()
    pt_route_platform_merge = pd.merge(pt_train_route_copy, pt_train_platform_copy, on='block_id')

    train_uturn_platforms = []
    route_platform =  pd.merge(pt_train_route_copy, pt_train_platform_copy, on='block_id')
    for lineID, line_route_platform in route_platform.groupby('line_id_x'):
        line_route_platform.sort_values(by=['sequence_no'], inplace=True)
        p = line_route_platform['platform_no'].values.tolist()[0]
        train_uturn_platforms.append((p, lineID))
    train_uturn_platforms = pd.DataFrame.from_records(train_uturn_platforms, columns=['platformno', 'lineid'])
    return train_uturn_platforms


def mrt_line_properties(pt_train_route):
    # Step 19: create mrt_line_properties table
    mrt_line_properties = pd.DataFrame()
    print(pt_train_route.columns)
    mrt_line_properties['line_id'] = pd.unique(pt_train_route['line_id'])
    mrt_line_properties['min_dwell_time_normal'] = [20] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['min_dwell_time_terminal'] = [60] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['min_dwell_time_interchange'] = [50] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['dwell_time_formula_first_coeff'] = [12.22] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['dwell_time_formula_second_coeff'] = [2.27] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['dwell_time_formula_third_coeff'] = [1.82] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['dwell_time_formula_fourth_coeff'] = [0.00062] *len(pd.unique(pt_train_route['line_id']))

    mrt_line_properties['safe_operation_distance_meter'] = [50] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['safe_operation_headway_sec'] = [90] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['min_dis_behind_unscheduled_train'] = [200] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['train_length'] = [138] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['train_capacity'] = [1600] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['distance_arriving_at_platform'] = [0.001] *len(pd.unique(pt_train_route['line_id']))
    mrt_line_properties['max_dwell_time'] = [120] *len(pd.unique(pt_train_route['line_id']))
    return mrt_line_properties


def train_fleet(pt_train_route):
    # Step 25: create train_fleet table
    train_fleet = pd.DataFrame()
    train_fleet['line'] = pd.unique(pt_train_route['line_id'])
    train_fleet['min_initial_id'] = [1] * len(pd.unique(pt_train_route['line_id']))
    train_fleet['max_initial_id'] = [5] * len(pd.unique(pt_train_route['line_id']))
    return train_fleet


def deltaTime(start, end):
    sStart = start.split(':')
    sEnd = end.split(':')
    sEnd = int(sEnd[0])*3600 + int(sEnd[1])*60 + int(sEnd[2])
    sStart = int(sStart[0])*3600 + int(sStart[1])*60 + int(sStart[2])
    deltaSeconds = sStart - sEnd
    return deltaSeconds

def formatSecond(deltaSeconds):
    totalSec = deltaSeconds %60
    totalMin = (deltaSeconds // 60) % 60
    totalHour = (deltaSeconds //3600) % 24
    total_time = datetime.time(int(totalHour), int(totalMin), int(totalSec))
    total_time =  total_time.strftime("%H:%M:%S")
    return total_time


# Neighbor station travel times
def transit_edge(weekday_train_seq): #TODO
    # columns = ['from_stn', 'to_stn', 'travel_time', 'type'] 'RTS', 'TRS'
    # train_platform_cols = ['platform_no', 'station_no', 'line_id', 'capacity', 'type', 'block_id', 'pos_offset', 'length']
    # dispatch_detialed_cols = ['trip_id','arrival_time','departure_time','stop_id','stop_sequence','service','service_id','stop_lat','stop_long','C_type']
    # dispatch = pd.merge(dispatch_detialed[['trip_id','arrival_time','departure_time', 'stop_id', 'platform_no']],
    #                     train_platform[['platform_no', 'station_no']], on='platform', how='left')
    # transit_df = []
    # for tripID, group in dispatch.groupby('trip_id'):
    #     from_stn = group.stop_id.tolist()[:-1]
    #     to_stn = from_to = group.stop_id.tolist()[:-1]
    # transit_df = pd.DataFrame.from_records(transit_df, columns=['from_stn', 'to_stn', 'travel_time'])

    # Step 23: create rail_transit_edge table
    print(weekday_train_seq.head(3))
    test = weekday_train_seq.copy()
    fro_stn = []
    to = []
    dur = []
    for name, group in weekday_train_seq.groupby('trip_id'):
        fro_stn += group['stop_id'][0:len(group)-1].tolist()
        to += group['stop_id'][1:len(group)].tolist()
        dur +=[ deltaTime(start, end) for start, end in list(zip(group['arrival_time'][1:], group['departure_time'][:-1]))]
        # dur += (group['arrival_time'][1:len(group)].as_matrix()- group['departure_time'][0:len(group)-1].as_matrix()).astype('timedelta64[s]').astype(int).tolist()

    d = {'from_stn': fro_stn,
         'to_stn': to,
         'travel_time': dur}
    rail_transit_edge = pd.DataFrame(d)
    rail_transit_edge = rail_transit_edge.groupby(['from_stn','to_stn']).mean().reset_index(level=[0,1])
    # rail_transit_edge['travel_time_format'] = rail_transit_edge.apply(lambda row: formatSecond(row.travel_time), axis=1)
    rail_transit_edge['type'] = ['RTS'] * len(rail_transit_edge)
    cols = ['from_stn','to_stn','travel_time','type']
    rail_transit_edge = rail_transit_edge[cols]
    return rail_transit_edge
