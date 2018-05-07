import pandas as pd
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

mergedStats()
