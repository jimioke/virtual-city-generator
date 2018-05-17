import pandas as pd
import geopandas as gpd
import random
from shapely.geometry import LineString, Point
from sklearn.utils import shuffle

LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'} #3857

dataBaseFolder = 'to_db/'
parking_cols = ['parking_id', 'segment_id', 'access_node', 'egress_node']
taxi_stand_cols = ['id', 'x', 'y', 'z', 'segment_id', 'length', 'section_offset', 'tags']
taxi_fleet_cols = ['vehicle_no', 'driver_id', 'longtitude_at_start_point', 'latitude_at_start_point',
                    'start_time', 'index', 'subscribed_controllers', 'shift_duration']

simmobilityFolder = '../network-from-OSM/Outputs/Auto_sprawl_drive_main_projected/'
simLatLong = '../network-from-OSM/Outputs/Auto_sprawl_drive_main/'

NUM_TAXI = 10000
NUM_PARKING = 400
NUM_TAXI_STAND = 1400
TAXI_STAND_LENGTH = 1000 #1100 VC avg
# num_taz = 1401


def get_taz_latLong():
    taz = gpd.read_file('taz/2010_Traffic_Analysis_Zones_TAZ_CensusTIGER.shp')
    taz = taz.to_crs(LAT_LONG_CRS)
    taz.to_file('taz/taz_latLong')


def taxi_fleet_nodes():
    sub_4 = set(random.sample(range(1, NUM_TAXI), NUM_TAXI//2))
    # rest are subsciber 16
    # time10 = [10*x for x in range(0, 100)]
    # time30 = [10*(len(time10)) + 30*x for x in range(1, NUM_TAXI+1-300)]
    time7 =  [7*x for x in range(NUM_TAXI)]
    # startTime = time10 + time30
    # random.shuffle(startTime)
    startTime = pd.Series(time7)
    # print(startTime[startTime.isnull()])
    def formatTime(time):
        seconds = int(time%60)
        minutes = int(time//60%60)
        hours = int(time//3600%24)
        timeFormatted = []
        for i in (hours, minutes, seconds):
            if i == 0:
                formatted = '00'
            elif i < 10:
                formatted = '0' + str(i)
            else:
                formatted = str(i)
            timeFormatted.append(formatted)
        return ':'.join(timeFormatted)

    nodes = pd.read_csv(simmobilityFolder + 'node-node-indexed-typed.csv')
    nodes = nodes[nodes.node_type != 1]

    taxi_start_locations = nodes.sample(NUM_TAXI)['id'].tolist()
    taxi_fleet = nodes[nodes.id.isin(taxi_start_locations)]
    taxi_fleet['longtitude_at_start_point'] = taxi_fleet.apply(lambda row: row.x, axis=1)
    taxi_fleet['latitude_at_start_point'] = taxi_fleet.apply(lambda row: row.y, axis=1)
    taxi_fleet = taxi_fleet[['longtitude_at_start_point', 'latitude_at_start_point']]
    taxi_fleet.reset_index(drop=True, inplace=True)
    taxi_fleet['start_time'] = startTime
    taxi_fleet['start_time'] = taxi_fleet.apply(lambda row: formatTime(row.start_time), axis=1)
    taxi_fleet['shift_duration'] = pd.Series([10]*len(taxi_fleet))
    taxi_fleet['int_index'] = pd.Series([int(i) for i in range(len(taxi_fleet))])
    taxi_fleet['str_index'] = taxi_fleet.apply(lambda row: NUM_TAXI*10 + row.int_index, axis=1)
    taxi_fleet['str_index'] = taxi_fleet.apply(lambda row: str(NUM_TAXI*10 + row.int_index), axis=1)
    taxi_fleet['subscribed_controllers'] = taxi_fleet.apply(lambda row: 4 if row.int_index in sub_4 else 16, axis=1)

    taxi_fleet['driver_id'] = taxi_fleet.apply(lambda row: row.str_index + '-' + str(row.subscribed_controllers), axis=1)
    def get_vehicleNo(row):
        if row.subscribed_controllers == 4:
            return 'AMD' + row.str_index
        elif row.subscribed_controllers == 16:
            return 'SHA' + row.str_index
    taxi_fleet['vehicle_no'] = taxi_fleet.apply(lambda row: get_vehicleNo(row), axis=1)
    taxi_fleet['index']  = taxi_fleet['int_index']
    taxi_fleet = taxi_fleet[taxi_fleet_cols]
    taxi_fleet.to_csv(dataBaseFolder + 'taxi_fleet.csv', index=False)

taxi_fleet_nodes()

def taxi_fleet():
    sub_4 = set(random.sample(range(1, NUM_TAXI), NUM_TAXI//2))
    # rest are subsciber 16
    time10 = [10*x for x in range(0, 300)]
    time30 = [10*(len(time10)) + 30*x for x in range(1, NUM_TAXI+1-300)]
    startTime = time10 + time30
    random.shuffle(startTime)
    startTime = pd.Series(startTime)
    def formatTime(time):
        # print(time)
        seconds = int(time%60)
        minutes = int(time//60%60)
        hours = int(time//3600%24)
        timeFormatted = []
        for i in (hours, minutes, seconds):
            if i == 0:
                formatted = '00'
            elif i < 10:
                formatted = '0' + str(i)
            else:
                formatted = str(i)
            timeFormatted.append(formatted)
        return ':'.join(timeFormatted)

    lanes = pd.read_csv(simLatLong + 'simmobility/lane-nodes.csv')
    lanes = lanes[lanes.seq_id == 1]

    taxi_start_locations = lanes.sample(NUM_TAXI)['id'].tolist()
    taxi_fleet = lanes[lanes.id.isin(taxi_start_locations)]

    taxi_fleet['longtitude_at_start_point'] = taxi_fleet.apply(lambda row: row.x, axis=1)
    taxi_fleet['latitude_at_start_point'] = taxi_fleet.apply(lambda row: row.y, axis=1)
    taxi_fleet = taxi_fleet[['longtitude_at_start_point', 'latitude_at_start_point']]
    taxi_fleet.reset_index(drop=True, inplace=True)
    taxi_fleet['start_time'] = startTime
    taxi_fleet['start_time'] = taxi_fleet.apply(lambda row: formatTime(row.start_time), axis=1)
    taxi_fleet['shift_duration'] = pd.Series([10]*len(taxi_fleet))
    taxi_fleet['int_index'] = pd.Series([int(i) for i in range(len(taxi_fleet))])
    taxi_fleet['str_index'] = taxi_fleet.apply(lambda row: NUM_TAXI*10 + row.int_index, axis=1)
    taxi_fleet['str_index'] = taxi_fleet.apply(lambda row: str(NUM_TAXI*10 + row.int_index), axis=1)
    taxi_fleet['subscribed_controllers'] = taxi_fleet.apply(lambda row: 4 if row.int_index in sub_4 else 16, axis=1)

    taxi_fleet['driver_id'] = taxi_fleet.apply(lambda row: row.str_index + '-' + str(row.subscribed_controllers), axis=1)
    def get_vehicleNo(row):
        if row.subscribed_controllers == 4:
            return 'AMD' + row.str_index
        elif row.subscribed_controllers == 16:
            return 'SHA' + row.str_index
    taxi_fleet['vehicle_no'] = taxi_fleet.apply(lambda row: get_vehicleNo(row), axis=1)
    taxi_fleet['index']  = taxi_fleet['int_index']
    taxi_fleet = taxi_fleet[taxi_fleet_cols]
    taxi_fleet.to_csv(dataBaseFolder + 'taxi_fleet.csv', index=False)
# taxi_fleet()

def getSegmentEndNodes(simFolder=simmobilityFolder):
    links = pd.read_csv(simFolder + 'link-attributes-indexed.csv') #id,road_type,category,from_node,to_node,road_name,tags,osmid
    links.rename(columns={'id':'link_id'}, inplace=True)
    segments = gpd.read_file('Segment_in_taz/Segment_in_taz.shp') # TZ_TXT segID, link_id
    segments = segments.merge(links[['link_id', 'from_node', 'to_node']], on=['link_id'])
    return segments[['segID', 'from_node', 'to_node', 'TZ_TXT']]


def constructSeqLine(df, idColumn='id', seqColumn='seq_id', x='x', y='y'):
    df = df.sort_values([seqColumn])
    grouped = df.groupby(idColumn)
    rows = []
    for name,group in grouped:
        line_coords = group[[x, y]]
        line = LineString(tuple(x) for x in line_coords.to_records(index=False))
        rows.append( (name, line) )
    return pd.DataFrame.from_records(rows, columns=[idColumn, 'geometry'])


def getRoadNetworkGeos(simFolder=simmobilityFolder, fromCRS=LAT_LONG_CRS, toCRS=BALTIMORE_CRS):
    segmentCoords = pd.read_csv(simFolder + 'segment-nodes.csv') #id,x,y,z,seq_id
    segmentGeo = constructSeqLine(segmentCoords)
    segmentGeo = gpd.GeoDataFrame(segmentGeo, crs=BALTIMORE_CRS)
    segmentGeo.to_file('SegmentGeoXY')
    print(segmentGeo.columns)
    return segmentGeo


def parking():
    # ['parking_id', 'segment_id', 'access_node', 'egress_node']
    segments = getSegmentEndNodes()
    segments = shuffle(segments)
    segments.drop_duplicates(subset=['TZ_TXT'], inplace=True)
    parking_segments = segments.sample(NUM_PARKING)['segID'].tolist()
    parking = segments[segments.segID.isin(parking_segments)]
    parking.rename(columns={'segID':'segment_id', 'from_node': 'access_node', 'to_node':'egress_node'}, inplace=True)
    parking.reset_index(drop=True, inplace=True)
    parking['parking_id'] = parking.index + 1
    parking = parking[parking_cols]
    parking.to_csv(dataBaseFolder + 'parking.csv', index=False)


def parking_location():
    nodes = gpd.read_file(simmobilityFolder + '/node_wgs84.shp')
    nodes['id'] = nodes['id'].astype('int')
    parking = pd.read_csv(dataBaseFolder + 'parking.csv')
    print('parking ', len(parking))
    parking['access_node'] = parking['access_node'].astype('int')
    parking = parking.merge(nodes, left_on='access_node', right_on = 'id', how='left')

    parking['x'] = parking.apply(lambda row: row.geometry.x, axis=1)
    parking['y'] = parking.apply(lambda row: row.geometry.y, axis=1)
    # parking = gpd.GeoDataFrame(parking, crs=LAT_LONG_CRS, geometry=parking['geometry'])
    parking.to_csv('parking_latLong.csv')


def taxi_stands(): # xy coordinate
    # ['id', 'x', 'y', 'z', 'segment_id', 'length', 'section_offset', 'tags']
    segments = gpd.read_file('Segment_in_taz/Segment_in_taz.shp')
    segments.crs = LAT_LONG_CRS
    segments = segments.to_crs(BALTIMORE_CRS)

    print('segments ', segments.columns)
    segments['id'] = segments['segID'].astype('int')
    # Filter out parking segments and find random segments
    segments = shuffle(segments)
    taxi_stands = segments.drop_duplicates(subset=['TZ_TXT'])
    taxi_stands['length'] = TAXI_STAND_LENGTH
    taxi_stands.rename(columns={'id':'segment_id'}, inplace=True)
    taxi_stands['section_offset'] = taxi_stands.apply(lambda row: row.geometry.length*0.8, axis=1)
    taxi_stands['location'] = taxi_stands.apply(lambda row: row.geometry.interpolate(0.2, normalized=True), axis=1)
    taxi_stands['x'] = taxi_stands.apply(lambda row: row.location.x, axis=1)
    taxi_stands['y'] = taxi_stands.apply(lambda row: row.location.y, axis=1)
    taxi_stands['z'] = 0
    taxi_stands['tags'] = ''
    taxi_stands.reset_index(drop=True, inplace=True)
    taxi_stands['id'] = taxi_stands.index + 1
    taxi_stands = taxi_stands[taxi_stand_cols]
    taxi_stands.to_csv(dataBaseFolder + 'taxi_stand.csv', index=False)
