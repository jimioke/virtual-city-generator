################################################################################
# Description: Clean and prepare Train GTFS files for creating SimMobility tables.
# Written by: Iveel Tsogsuren
################################################################################
import pandas as pd
import geopandas as gpd
import psycopg2,pdb
from shapely.geometry import Point, LineString, MultiPoint, MultiLineString
from shapely.ops import transform
from functools import partial
import pyproj

gtfsFolder = 'MTA-MD/'
trainGTFS = 'Outputs/train_gtfs/'

LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}
CURRENT_CRS = BALTIMORE_CRS

trip_cols = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name', 'direction_id', 'block_id', 'shape_id', 'wheelchair_accessible']
# char var(50),char var(50),char var(50),char var(150),char var(20),int, char var(20),char var(20),int
shape_cols = ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled']
# char var (20), double pre, double pre, int, char var (10)
stoptime_cols = ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'stop_headsign', 'pickup_type', 'drop_off_type']
# char var (50), char var (20),char var (20),char var (150),int, char var (20),int, int
stop_cols = ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon', 'zone_id', 'stop_url', 'location_type', 'parent_station', 'wheelchair_boarding']
# char var (150),char var (150),char var (150),char var (150),double pre, double pre, char var (50), char var (50),int

# Using QGIS, find a point nearby one of the ends for each visually unique shape.
# We use these points to determine direction and opposite directional shapes.
ROUTE_END = { # route_id: an approximate end point.
10196: Point(434842.804,181005.484),
10210: Point(428314.518,168542.393),
10222: Point(399629.628,136890.100),
10223: Point(399629.628,136890.100),
10224: Point(399629.628,136890.100),
}

# For each route, find a pair of opposite shapes' shape_id.
# You can use findLongestLines function with ROUTE_END.
Route_to_shapes = {
10196: ['L5', 'L1'],
10210: ['L16', 'L23'],
10222: ['L51', 'L40'],
10223: ['L89', 'L75'],
10224: ['L153', 'L143'],
}

def constructSeqLine(df, idColumn='id', seqColumn='seq_id', x='x', y='y'):
    df = df.sort_values([seqColumn])
    grouped = df.groupby(idColumn)
    rows = []
    for name,group in grouped:
        line_coords = group[[x, y]]
        line = LineString(tuple(x) for x in line_coords.to_records(index=False))
        rows.append( (name, line) )
    return pd.DataFrame.from_records(rows, columns=[idColumn, 'geometry'])

def filterTrainGTFS(gtfsFolder=gtfsFolder, outputFolder=filteredTrainFolder,
        route='routes.txt', trip='trips.txt', stoptime='stop_times.txt',
        shape='shapes.txt', stop='stops.txt'):
    """
    Filter out train routes from GTFS files.

    Parameters
    ----------
    gtfsFolder : Original gtfs files folder
    outputFolder : Folder for filtered out train GTFS files.
    route, trip, stoptime, shape, stop: standard GTFS files.
    """
    # Read gtfs files
    route_df = pd.read_csv(gtfsFolder  + route)
    trip_df = pd.read_csv(gtfsFolder  + trip)
    stoptime_df = pd.read_csv(gtfsFolder  + stoptime)
    shape_df = pd.read_csv(gtfsFolder + shape)
    stop_df = pd.read_csv(gtfsFolder + stop)
    # gtfs_stop_df = pd.read_csv(gtfsFolder + 'stops.txt')
    print('columns route_df', route_df.columns)
    print('columns trip_df', trip_df.columns)
    print('columns stoptime_df', stoptime_df.columns)
    print('columns shape_df', shape_df.columns)
    print('columns stop_df', stop_df.columns)

    # Filter out train routes, trips, shapes and stops.
    route_df = route_df[route_df.route_type != 3]
    train_routes = route_df.route_id.tolist()
    trip_df = trip_df[trip_df.route_id.isin(train_routes)]
    trip_df.sort_values(by=['route_id', 'trip_id'], inplace=True)
    train_trips = list(trip_df.trip_id.unique())
    train_shapes = list(trip_df.shape_id.unique())

    shape_df = shape_df[shape_df.shape_id.isin(train_shapes)]
    shape_df.sort_values(by=['shape_id', 'shape_pt_sequence'], inplace=True)

    stoptime_df = stoptime_df[stoptime_df.trip_id.isin(train_trips)]
    stoptime_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)

    train_stops = list(stoptime_df.stop_id.unique())
    stop_df = stop_df[stop_df.stop_id.isin(train_stops)]
    stop_df.sort_values(by=['stop_id'])

    # Rename IDs
    trip_names = dict(zip(train_trips, ['T' + str(i+1) for i in range(len(train_trips))]))
    shape_names = dict(zip(train_shapes, ['L' + str(i+1) for i in range(len(train_shapes))]))
    stop_names = dict(zip(train_stops, ['S' + str(i+1) for i in range(len(train_stops))]))
    trip_df['trip_id'] = trip_df.apply(lambda row: trip_names[row.trip_id], axis=1)
    stoptime_df['trip_id'] = stoptime_df.apply(lambda row: trip_names[row.trip_id], axis=1)

    stoptime_df['stop_id'] = stoptime_df.apply(lambda row: stop_names[row.stop_id], axis=1)
    stop_df['stop_id'] = stop_df.apply(lambda row: stop_names[row.stop_id], axis=1)

    trip_df['shape_id'] = trip_df.apply(lambda row: shape_names[row.shape_id], axis=1)
    shape_df['shape_id'] = shape_df.apply(lambda row: shape_names[row.shape_id], axis=1)

    # Put columns in right order
    trip_df = trip_df[trip_cols]
    stoptime_df = stoptime_df[stoptime_cols]
    shape_df = shape_df[shape_cols]
    stop_df = stop_df[stop_cols]

    route_df.to_csv(outputFolder+'route.csv',index=False)
    trip_df.to_csv(outputFolder+'trips_pre.csv',index=False)
    stoptime_df.to_csv(outputFolder+'stop_times.csv',index=False)
    shape_df.to_csv(outputFolder+'shapes.csv',index=False)
    stop_df.to_csv(outputFolder+'stops.csv',index=False)


def getGTFS(gtfsFolder=trainGTFS, route='route.csv', trip='trips_pre.csv',
            stoptime='stop_times.csv', shape='shapes.csv', stop='stops.csv'):
    """ Read GTFS files into pandas dataframes. """
    route_df = pd.read_csv(gtfsFolder  + route)
    trip_df = pd.read_csv(gtfsFolder  + trip)
    stoptime_df = pd.read_csv(gtfsFolder  + stoptime)
    shape_df = pd.read_csv(gtfsFolder + shape)
    stop_df = pd.read_csv(gtfsFolder + stop)
    return route_df, trip_df, stoptime_df, shape_df, stop_df

def findLongestLines(trainGTFS=trainGTFS, currentCRS=CURRENT_CRS, keep_nlargest=5):
    """
    Find shapes' in and out directions based on route end points. Then find
    the N longest (lenght and number of stops) trips for each route.

    Parameters
    ----------
    trainGTFS : A folder of train gtfs which we would process.
    currentCRS : Train GTFS x, y crs system.
    keep_nlargest : Number of routes we would want to keep.
    """
    # Read gtfs files
    route_df, trip_df, stoptime_df, shape_df, stop_df = getGTFS(gtfsFolder=trainGTFS)
    shape_df = shape_df.merge(trip_df[['direction_id', 'shape_id', 'route_id', 'trip_id']], on='shape_id', how='left')
    shape_df.index = shape_df.shape_id
    def properDirection(row, routeID):
        start = Point(row.geometry.coords[0])
        end = Point(row.geometry.coords[-1])
        relative = ROUTE_END[routeID]
        return int(relative.distance(start) > relative.distance(end))

    # For visually investigating diverging routes
    # routes_to_two_dir_lines = {}
    # for indx, tripID in enumerate(stoptime_df.trip_id.unique(),1):
    #     stoptime_line = stoptime_df[shape_df.trip_id == tripID]
    #     shapeGeo = constructSeqLine(shape_line, idColumn= 'shape_id', seqColumn='shape_pt_sequence', x='shape_pt_lon', y='shape_pt_lat')
    #     shapeGeo = gpd.GeoDataFrame(shapeGeo, crs=LAT_LONG_CRS)
    #     shapeGeo = shapeGeo.to_crs(CURRENT_CRS)
    #     shapeGeo['direction'] = shapeGeo.apply(lambda row: properDirection(row, routeID), axis=1)
    #     shapeGeo['length'] = shapeGeo.apply(lambda row: row.geometry.length, axis=1)
    #     print('shape columns ', shapeGeo.columns)

    # For visually investigating diverging routes
    routes_to_two_dir_lines = {}
    trip_num_stops = stoptime_df.groupby('trip_id')['stop_id'].apply(lambda row: len(list(row)))
    trip_df['num_stops'] = trip_df.apply(lambda row: trip_num_stops.get(row.trip_id), axis=1)
    # Shape direction and length
    for indx, routeID in enumerate(shape_df.route_id.unique(),1):
        shape_line = shape_df[shape_df.route_id == routeID]
        shapeGeo = constructSeqLine(shape_line, idColumn= 'shape_id', seqColumn='shape_pt_sequence', x='shape_pt_lon', y='shape_pt_lat')
        shapeGeo = gpd.GeoDataFrame(shapeGeo, crs=LAT_LONG_CRS)
        shapeGeo = shapeGeo.to_crs(CURRENT_CRS)
        shapeGeo['shape_direction'] = shapeGeo.apply(lambda row: properDirection(row, routeID), axis=1)
        shapeGeo['length'] = shapeGeo.apply(lambda row: row.geometry.length, axis=1)

        trips = trip_df.merge(shapeGeo, on='shape_id', how='inner')
        trips.sort_values(by=['length', 'num_stops'], inplace=True)
        # print('most frequent ', trips.groupby(['length', 'num_stops'])['trip_id'].apply(list)) #.apply(lambda row: len(list(row))))
        trips_in = trips[trips.shape_direction == 1]
        trips_out = trips[trips.shape_direction == 0]

        trips_in = trips_in.nlargest(keep_nlargest, 'length', keep='first')
        trips_out = trips_out.nlargest(keep_nlargest, 'length', keep='first')
        print('#### route ', routeID)
        print('0 direction \n', trips_in[['length', 'shape_id', 'num_stops']])
        print('1 direction \n', trips_out[['length', 'shape_id', 'num_stops']])
        # Choose two directional shapes with the same number of stops
        # Shapefiles for investigating theses longest routes
        # shapeIn.to_file('Routes_longest/' + str(indx) + '_' + str(routeID) + '_dir0.shp')
        # shapeOut.to_file('Routes_longest/' + str(indx) + '_' + str(routeID) + '_dir1.shp')
        # routes_to_two_dir_lines[routeID] = (shapeIn.shape_id.values[0], shapeOut.shape_id.values[0])
    return routes_to_two_dir_lines

def createLines(routes_to_two_dir_lines=Route_to_shapes,
                outputFolder='Outputs/clean_gtfs/'):
    """
    Make opposite shapes geometrically correcly reversed and find their stoptimes.

    Parameters
    ----------
    routes_to_two_dir_lines : {Route: (shape_id1, shape_id2)} where shape_id2
                             has a reversed shape of shape_id1.
    outputFolder : A folder where we output filtered and correctly directioned
                    train gtfs files.
    """
    route_df, trip_df, stoptime_df, shape_df, stop_df = getGTFS()

    # Create shapes
    all_shapes = []
    for routeID, line_shapeIDs in routes_to_two_dir_lines.items():
        oneway = shape_df[shape_df.shape_id == line_shapeIDs[0]]
        num_points = oneway.shape_pt_sequence.max()
        total_dist =  oneway.shape_dist_traveled.max()
        # Construct a reversed shape from oneway for the sake of consistency.
        otherway = oneway.copy()
        otherway['shape_id'] = line_shapeIDs[1]
        otherway['shape_pt_sequence'] = otherway.apply(lambda row: num_points - row.shape_pt_sequence + 1, axis=1)
        otherway['shape_dist_traveled'] = otherway.apply(lambda row: total_dist - row.shape_dist_traveled, axis=1)
        all_shapes +=  [oneway, otherway]
    all_shapes = pd.concat(all_shapes)

    # Create stop_times (trips must have the same number of stops)
    all_stoptimes = []
    stoptime_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)
    for routeID, line_shapeIDs in routes_to_two_dir_lines.items():
        oneway = trip_df[trip_df.shape_id == line_shapeIDs[0]]
        stoptime1 = stoptime_df[stoptime_df.trip_id.isin(oneway.trip_id.unique())]
        # determine stops
        onewayStops = stoptime1.groupby('trip_id')['stop_id'].apply(list).values[0]
        stoptime1['stop_id'] = stoptime1.apply(lambda row: onewayStops[row.stop_sequence-1], axis=1)

        otherway = trip_df[trip_df.shape_id == line_shapeIDs[1]]
        stoptime2 = stoptime_df[stoptime_df.trip_id.isin(otherway.trip_id.unique())]
        stoptime2['stop_id'] = stoptime2.apply(lambda row: onewayStops[-1*row.stop_sequence], axis=1)
        all_stoptimes += [stoptime1, stoptime2]
    all_stoptimes = pd.concat(all_stoptimes)

    all_stops = stop_df[stop_df.stop_id.isin(all_stoptimes.stop_id.unique())]
    all_trips = trip_df[trip_df.shape_id.isin(all_shapes.shape_id.unique())]

    route_df.to_csv(outputFolder + 'route.csv', index=False)
    all_trips.to_csv(outputFolder + 'trips.csv', index=False)
    all_shapes.to_csv(outputFolder + 'shapes.csv', index=False)
    all_stoptimes.to_csv(outputFolder + 'stop_times.csv', index=False)
    all_stops.to_csv(outputFolder + 'stops.csv', index=False)
