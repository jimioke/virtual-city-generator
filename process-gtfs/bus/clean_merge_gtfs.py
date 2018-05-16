import pandas as pd
import geopandas as gpd
import os
import pandas as pd, datetime

gtfsInputDir = 'gtfs-source/'
gtfsOutputDir = 'clean-gtfs/'

def gtfsBasedOnRoute(routeDF, shapeDF, stoptimeDF, tripDF, stopsDF, outFolder):
    trip = tripDF.merge(routeDF[['route_id']], on='route_id')
    stoptime = stoptimeDF.merge(trip[['trip_id']], on='trip_id')
    stops = stopsDF.merge(stoptime[['stop_id']], on='stop_id')
    shape = shapeDF.merge(trip[['shape_id']], on='shape_id')
    print("# Unique route IDs: {} from routes, {} from trips".format(len(routeDF.route_id.unique()), len(trip.route_id.unique())))
    print("# Unique trip IDs: {} from trip, {} from stoptime".format(len(trip.trip_id.unique()), len(stoptime.trip_id.unique())))
    print("# Unique stop IDs: {} from stop, {} from stoptime".format(len(stops.stop_id.unique()), len(stoptime.stop_id.unique())))
    print("# Unique shape IDs: {}".format(len(shape.shape_id.unique())))

    routeDF.to_csv(outFolder + 'route.csv', index=False)
    shape.to_csv(outFolder + 'shape.csv', index=False)
    stoptime.to_csv(outFolder + 'stoptime.csv', index=False)
    trip.to_csv(outFolder + 'trip.csv', index=False)
    stops.to_csv(outFolder + 'stops.csv', index=False)
    return shape, stoptime, trip, stops


def prepareCleanedBusRoute(gtfsFolder, pre='', stopOffSet=0, inputDir=gtfsInputDir, outDir=gtfsOutputDir):
    inFolder = inputDir + gtfsFolder
    outFolder = outDir + gtfsFolder + '/'
    route_columns= ['route_id', 'route_type']
    trip_columns= ["route_id", 'service_id', "trip_id", "direction_id", "shape_id", "service_id"]
    shape_columns= ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"]
    stoptime_columns= ["trip_id", "stop_id", "stop_sequence", "arrival_time"]
    stop_columns= ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']

    route_df = pd.read_csv(inFolder + '/routes.txt')
    shape_df = pd.read_csv(inFolder + '/shapes.txt')
    stoptime_df = pd.read_csv(inFolder + '/stop_times.txt')
    trip_df = pd.read_csv(inFolder + '/trips.txt')
    stops_df = pd.read_csv(inFolder + '/stops.txt')
    # calendar_df = pd_read_csv(inFolder + '/calendar.txt')
    #stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_timezone,wheelchair_boarding

    # Filter out columns
    route_df = route_df[route_columns]
    shape_df = shape_df[shape_columns]
    stoptime_df = stoptime_df[stoptime_columns]
    trip_df = trip_df[trip_columns]

    # Cleaning the routes file
    print('##################### PREPARING : ', gtfsFolder, '#####################')
    print("1. Routes Summary......................................................")
    print("# null values in routes: {}".format(route_df.isnull().sum().sum()))
    if route_df.isnull().sum().sum() > 0:
        route_df = route_df.dropna()
        print("Null values dropped................................................")
    print('all type ----', len(route_df))
    rail_route_df = route_df[route_df.route_type != 3]
    route_df = route_df[route_df.route_type == 3]
    print("# unique bus routes: {}".format(len(route_df)))

    # Cleaning the trips file
    print("2. Trips Summary.......................................................")
    print("# null values in trips: {}".format(trip_df.isnull().sum().sum()))
    if trip_df.isnull().sum().sum() > 0:
        trip_df = trip_df.dropna()
        print("Null values dropped................................................")
    print("# unique routes: {}".format(len(trip_df.route_id.unique())))
    print("# unique trips: {}".format(len(trip_df.trip_id.unique())))

    # Cleaning the shapes file
    print("3. Shapes Summary......................................................")
    print("# null values in shapes: {}".format(shape_df.isnull().sum().sum()))
    if shape_df.isnull().sum().sum() > 0:
        shape_df = shape_df.dropna()
        print("Null values dropped................................................")
    print("# unique shapes: {}".format(len(shape_df.shape_id.unique())))

    # Cleaning the stop times file
    print("4. Stop Times Summary..................................................")
    print("# null values in stop times: {}".format(stoptime_df.isnull().sum().sum()))
    if stoptime_df.isnull().sum().sum() > 0:
        stoptime_df = stoptime_df.dropna()
        print("Null values dropped")
    print("# unique trips: {}".format(len(stoptime_df.trip_id.unique())))
    print("# unique stops: {}".format(len(stoptime_df.stop_id.unique())))

    def strID(raw_id):
        try:
            raw_id = int(raw_id)
            return str(raw_id)
        except:
            return str(raw_id)

    # Differentiate route id, trip id, stop id, shape id
    route_df['route_id'] = route_df.apply(lambda row: pre + strID(row.route_id), axis=1)
    trip_df['route_id'] = trip_df.apply(lambda row: pre + strID(row.route_id), axis=1)

    trip_df['trip_id'] = trip_df.apply(lambda row: pre + strID(row.trip_id), axis=1)
    stoptime_df['trip_id'] = stoptime_df.apply(lambda row: pre + strID(row.trip_id), axis=1)

    uni_stopid = list(stops_df.stop_id.unique())
    uni_stopid = dict(zip(uni_stopid, range(stopOffSet, len(uni_stopid) + stopOffSet)))
    stoptime_df['stop_id'] = stoptime_df.apply(lambda row: uni_stopid[row.stop_id], axis=1)
    stops_df['stop_id'] = stops_df.apply(lambda row: uni_stopid[row.stop_id], axis=1)

    trip_df['shape_id'] = trip_df.apply(lambda row: pre + strID(row.shape_id), axis=1)
    shape_df['shape_id'] = shape_df.apply(lambda row: pre + strID(row.shape_id), axis=1)


    if not os.path.exists(outFolder):
        os.makedirs(outFolder)

    if len(rail_route_df) == 0:
        return {'route':route_df,
                'shape':shape_df,
                'stoptime':stoptime_df,
                'trip':trip_df,
                'stops':stops_df}, stops_df.stop_id.max()

    print('rail_route_df columns  ', rail_route_df.columns, rail_route_df.head(3))
    rail_route_df['route_id'] = rail_route_df.apply(lambda row: pre + str(row.route_id), axis=1)


    return {'route':route_df,
            'shape':shape_df,
            'stoptime':stoptime_df,
            'trip':trip_df,
            'stops':stops_df}, stops_df.stop_id.max()


def cleanAndMergeGTFS(inputDir=gtfsInputDir, outDir=gtfsOutputDir):
    gtfsSubfolders = ['AnneArundel', 'Carrol', 'Harford', 'Howard', 'MTA-MD', 'QueenAnne']
    prefex = ['aPre_', 'cPre_', 'harPre_', 'howPre_', 'mtaPre_', 'qaPre_']
    # gtfsSubfolders = ['MTA-MD']
    # prefex = ['mtaPre_']

    outFiles = ['route', 'shape', 'stoptime', 'trip', 'stops']
    all_dfs = dict(zip(outFiles, [[] for i in range(len(outFiles))]))
    # print(all_dfs)
    mergeFolder = outDir + 'Merged_all/'
    stopOffSet = 0
    for index, gtfs in enumerate(gtfsSubfolders):
        pre = prefex[index]
        DFS, stopIDmax = prepareCleanedBusRoute(gtfs, pre=pre, stopOffSet=stopOffSet, inputDir=gtfsInputDir, outDir=gtfsOutputDir)
        stopOffSet = stopIDmax + 1
        # Note source
        for key, df in DFS.items():
            # print(df)
            df['source'] = gtfs #df.apply(lambda row: gtfs, axis=1)
            all_dfs[key].append(df)
    for key, df_list in all_dfs.items():
        merged_dfs =  pd.concat(df_list)
        merged_dfs.to_csv(mergeFolder + key + '.csv', index=False)


def mergedStats(outDir=gtfsOutputDir):
    mergeFolder = outDir + 'Merged/'
    busFolder = outDir + 'MergedBus/'
    all_routes = pd.read_csv(mergeFolder + 'route.csv', low_memory=True)
    all_shapes = pd.read_csv(mergeFolder + 'shape.csv', low_memory=True)
    all_stoptime = pd.read_csv(mergeFolder + 'stoptime.csv', low_memory=True)
    all_trips = pd.read_csv(mergeFolder + 'trip.csv', low_memory=True)
    all_stops = pd.read_csv(mergeFolder + 'stops.csv', low_memory=True)

    route_columns= ['route_id', 'route_type']
    trip_columns= ["route_id", "trip_id", "direction_id", "shape_id", "service_id"]
    shape_columns= ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"]
    stoptime_columns= ["trip_id", "stop_id", "stop_sequence", "arrival_time"]
    stop_columns= ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']

    shape_ids = all_shapes.shape_id.unique()
    shapeIDmap = dict(zip(shape_ids, ['B' + str(i) for i in range(1, len(shape_ids)+1)]))
    all_shapes['shape_id'] = all_shapes.apply(lambda row: shapeIDmap[row.shape_id], axis=1)
    all_trips['shape_id'] = all_trips.apply(lambda row: shapeIDmap[row.shape_id], axis=1)

    print('Number of sources ', all_routes.source.unique())
    print('Number of routes ', len(all_routes.route_id.unique()))
    print('Number of shapes ', len(all_shapes.shape_id.unique()))
    print('Number of (trip_id) in stoptime ', len(all_stoptime.trip_id.unique()))
    print('Number of trips ', len(all_trips.trip_id.unique()))
    print('Number of stops ', len(all_stops.stop_id.unique()))

    bus_routes = all_routes.route_id.unique()
    all_trips = all_trips[all_trips.route_id.isin(bus_routes)]
    bus_shapes = all_trips.shape_id.unique()
    bus_trips = all_trips.trip_id.unique()
    all_shapes = all_shapes[all_shapes.shape_id.isin(bus_shapes)]
    all_stoptime = all_stoptime[all_stoptime.trip_id.isin(bus_trips)]
    bus_stops = all_stoptime.stop_id.unique()
    all_stops = all_stops[all_stops.stop_id.isin(bus_stops)]
    all_shapes.sort_values(by=['shape_id', 'shape_pt_sequence'], inplace=True)
    all_stoptime.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)

    print('#################  after clean (keeping bus trips) ######################')
    print('Number of sources ', len(all_routes.source.unique()))
    print('Number of routes ', len(all_routes.route_id.unique()))
    print('Number of shapes ', len(all_shapes.shape_id.unique()))
    print('Number of (trip_id) in stoptime ', len(all_stoptime.trip_id.unique()))
    print('Number of trips ', len(all_trips.trip_id.unique()))
    print('Number of stops ', len(all_stops.stop_id.unique()))

    all_routes.to_csv(busFolder + 'routes.txt', index=False)
    all_shapes.to_csv(busFolder + 'shapes.txt', index=False)
    all_stoptime.to_csv(busFolder + 'stop_times.txt', index=False)
    all_trips.to_csv(busFolder + 'trips.txt', index=False)
    all_stops.to_csv(busFolder + 'stops.txt', index=False)

# mergedStats()
route_columns= ['route_id', 'route_type']
trip_columns= ["route_id", 'service_id', "trip_id", "direction_id", "shape_id", "service_id"]
shape_columns= ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"]
stoptime_columns= ["trip_id", "stop_id", "stop_sequence", "arrival_time"]
stop_columns= ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'parent_station']

def clean_without_merge():
    gtfsInputDir= 'gtfs_israel/'
    gtfsOutputDir = 'gtfs_clean_israel/'
    stops_in_boundary = gpd.read_file(gtfsInputDir + 'stops_in_area/stops_in_area.shp')
    stops_in_boundary['stop_lon'] = stops_in_boundary.apply(lambda r: r.geometry.x, axis=1)
    stops_in_boundary['stop_lat'] = stops_in_boundary.apply(lambda r: r.geometry.y, axis=1)
    stops_in_boundary['parent_station'] =  ''
    stop_times = pd.read_csv(gtfsInputDir + 'stop_times.txt')
    trips = pd.read_csv(gtfsInputDir + 'trips.txt')
    routes = pd.read_csv(gtfsInputDir + 'routes.txt')
    shapes = pd.read_csv(gtfsInputDir + 'shapes.txt')
    # Filter out columns
    routes = routes[route_columns]
    stop_times = stop_times[stoptime_columns]
    trips = trips[trip_columns]
    stops_in_boundary = stops_in_boundary[stop_columns]
    shapes = shapes[shape_columns]

    # Integerize ids
    stop_times['stop_id'] = stop_times['stop_id'].astype(int)
    stop_times['trip_id'] = stop_times['trip_id'].astype(int)
    trips['trip_id'] = trips['trip_id'].astype(int)
    trips['route_id'] = trips['route_id'].astype(int)
    routes['route_id'] = routes['route_id'].astype(int)
    shapes['shape_id'] = shapes['shape_id'].astype(int)
    stops_in_boundary['stop_id'] = stops_in_boundary['stop_id'].astype(int)
    print('Number of trips ', len(trips.trip_id.unique()))
    print('Number of routes ', len(routes.route_id.unique()))

    # Find trips which go through the area of interest.
    stops = set(stops_in_boundary['stop_id'].tolist())
    stop_times = stop_times[stop_times['stop_id'].isin(stops)]
    trips_to_keep = set(stop_times['trip_id'].tolist())
    filtered_trips = trips[trips['trip_id'].isin(trips_to_keep)]
    routes_to_keep = filtered_trips['route_id'].unique()
    filtered_routes = routes[routes['route_id'].isin(routes_to_keep)]


    train_routes = filtered_routes[filtered_routes['route_type'] != 3]
    bus_routes = filtered_routes[filtered_routes['route_type'] == 3]

    bus_route_ids  = bus_routes['route_id'].unique()
    train_route_ids  = train_routes['route_id'].unique()

    bus_trips = filtered_trips[filtered_trips['route_id'].isin(bus_route_ids)]
    train_trips = filtered_trips[filtered_trips['route_id'].isin(train_route_ids)]

    bus_trip_ids = bus_trips['trip_id'].unique()
    bus_shape_ids = bus_trips['shape_id'].unique()
    train_trip_ids = train_trips['trip_id'].unique()
    train_shape_ids = train_trips['shape_id'].unique()

    # Filter out stoptimes, shapes
    bus_stop_times = stop_times[stop_times['trip_id'].isin(bus_trip_ids)]
    bus_shapes = shapes[shapes['shape_id'].isin(bus_shape_ids)]
    train_stop_times = stop_times[stop_times['trip_id'].isin(train_trip_ids)]
    train_shapes = shapes[shapes['shape_id'].isin(train_shape_ids)]

    # Filter out stops
    bus_stop_ids = bus_stop_times['stop_id'].unique()
    train_stop_ids = train_stop_times['stop_id'].unique()
    bus_stops = stops_in_boundary[stops_in_boundary['stop_id'].isin(bus_stop_ids)]
    train_stops = stops_in_boundary[stops_in_boundary['stop_id'].isin(train_stop_ids)]


    print('Number of filtered bus trips ', len(bus_trip_ids))
    print('Number of filtered train trips ', len(train_trip_ids))
    print('Number of filtered bus stops ', len(bus_stop_ids))
    print('Number of filtered train stops ', len(train_stop_ids))

    # Write train and bus gtfs files
    bus_trips.to_csv(gtfsOutputDir + '/bus/trips.txt', index=False)
    bus_routes.to_csv(gtfsOutputDir + '/bus/routes.txt', index=False)
    bus_stop_times.to_csv(gtfsOutputDir + '/bus/stop_times.txt', index=False)
    bus_stops.to_csv(gtfsOutputDir + '/bus/stops.txt', index=False)
    bus_shapes.to_csv(gtfsOutputDir + '/bus/shapes.txt', index=False)

    train_trips.to_csv(gtfsOutputDir + '/train/trips.txt')
    train_routes.to_csv(gtfsOutputDir + '/train/routes.txt')
    train_stop_times.to_csv(gtfsOutputDir + '/train/stop_times.txt', index=False)
    train_stops.to_csv(gtfsOutputDir + '/train/stops.txt', index=False)
    train_shapes.to_csv(gtfsOutputDir + '/train/shapes.txt', index=False)


    # print(stops_in_boundary.columns)
    # print(stops_in_boundary.head(2))

# clean_without_merge()
gtfsInputDir = 'gtfs_source_small_example/gtfs-QueenAnne/'
gtfsInputDir = 'gtfs_israel/'
def clean_missing_time(inFile='stop_times_full.txt'):
    stoptime_df = pd.read_csv(gtfsInputDir + inFile)
    print('original stop time ', len(stoptime_df))
    stoptime_df = stoptime_df.dropna()
    stoptime_df.to_csv(gtfsInputDir + 'stop_times.txt')
    print('cleaned stop time ', len(stoptime_df))
clean_missing_time()
