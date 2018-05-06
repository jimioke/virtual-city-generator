import pandas as pd

gtfsFolder = 'gtfs-QueenAnne/'
outFolder ='cleaned_gtfs/'
def readGTFS():
    # read
    gtfs_trips_df = pd.read_csv(outFolder  + 'trip.csv', index_col=['trip_id'])
    gtfs_stoptime_df = pd.read_csv(outFolder  + 'stoptime.csv')
    gtfs_shape_df = pd.read_csv(outFolder + 'shape.csv')
    gtfs_stop_df = pd.read_csv(gtfsFolder + 'stops.txt')

    gtf = gtfs_stoptime_df.groupby('trip_id')['stop_id'].apply(list)
    gtf = gtf.apply(lambda l: [str(e) for e in l])
    gtf = gtf.apply(lambda l: "&".join(l))
    gtf.drop_duplicates(inplace=True)
    # print(gtf['County Ride 1A_T01'] == gtf['County Ride 1B_T01'])
    print(gtf.keys())

    # for name, stops in allStops.groupby('trip_id'):


    return gtfs_trips_df, gtfs_stoptime_df, gtfs_shape_df, gtfs_stop_df

readGTFS()
def prepareCleanedBusRoute(gtf=gtfsFolder):
    route_columns= ['route_id', 'route_type']
    trip_columns= ["route_id", "trip_id", "direction_id", "shape_id", "service_id"]
    shape_columns= ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"]
    stoptime_columns= ["trip_id", "stop_id", "stop_sequence", "arrival_time"]
    base_columns= ["ID", "FNODE", "TNODE", "ctps_ID", "NB_LANES", "CAPACITY", "LinkCat", "DIRECTION", "LENGTH"]

    route_df = pd.read_csv(gtf + '/routes.txt')
    shape_df = pd.read_csv(gtf + '/shapes.txt')
    stoptime_df = pd.read_csv(gtf + '/stop_times.txt')
    trip_df = pd.read_csv(gtf + '/trips.txt')

    # Filter out columns
    route_df = route_df[route_columns]
    shape_df = shape_df[shape_columns]
    stoptime_df = stoptime_df[stoptime_columns]
    trip_df = trip_df[trip_columns]

    route_df.to_csv(outFolder + 'route.csv', index=False)
    shape_df.to_csv(outFolder + 'shape.csv', index=False)
    stoptime_df.to_csv(outFolder + 'stoptime.csv', index=False)
    trip_df.to_csv(outFolder + 'trip.csv', index=False)

# prepareCleanedBusRoute()
