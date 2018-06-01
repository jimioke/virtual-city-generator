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


# PREPARE SIMMOBILITY
simFolder = 'Auto_sprawl_drive_main/simmobility/'
gtfsFolder = 'clean-gtfs/MergedBus/'
processFolder = 'process_big/'
databaseFolder = 'to_db_big/'
CURRENT_CRS =  BALTIMORE_CRS

# Bus tables
# pt_bus_routes
# pt_bus_dispatch_freq
# pt_bus_stops

def test_route_segment_connectivity():
    segmentGraph = gpd.read_file(processFolder + 'segmentsWithNodes/segmentsWithNodes.shp')
    pt_bus_routes = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')
    pt_bus_routes = pt_bus_routes.merge(segmentGraph, left_on='section_id', right_on='id', how='left')

    pt_bus_routes.sort_values(by=['route_id', 'sequence_no'], inplace=True)
    segmentStarter = pt_bus_routes.groupby('route_id')['from_node'].apply(list)
    segmentEnder = pt_bus_routes.groupby('route_id')['to_node'].apply(list)
    matching = segmentStarter.combine(segmentEnder, lambda starter, ender: 1 if starter[1:] == ender[:-1] else 0)
    assert(matching.sum() == len(matching))
    print('All route segments are consequent')


def test_route_consistency():
    pt_bus_routes = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')
    pt_bus_dispatch_freq = pd.read_csv(databaseFolder + 'pt_bus_dispatch_freq.csv')
    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')

    ROUTES_bus_routes = set(pt_bus_routes.route_id.unique())
    ROUTES_bus_dispatch_freq = set(pt_bus_dispatch_freq.route_id.unique())
    ROUTES_bus_stops = set(pt_bus_stops.route_id.unique())
    print(len(ROUTES_bus_routes), len(ROUTES_bus_dispatch_freq), len(ROUTES_bus_stops))
    # TODO: 139 128!!!
    assert( ROUTES_bus_routes == ROUTES_bus_stops)
    assert( ROUTES_bus_routes == ROUTES_bus_dispatch_freq)
    print('All routes are presented in tables')

def test_busstop_consistency():
    pt_bus_routes = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')
    bus_stops = pd.read_csv(databaseFolder + 'bus_stop.csv')
    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_stops.csv')

    pt_bus_stops = pt_bus_stops.merge(bus_stops, left_on='stop_code', right_on='id', how='left')

    route_segments = pt_bus_routes.groupby('route_id')['section_id'].apply(list)
    route_stop_segments = pt_bus_stops.groupby('route_id')['section_id'].apply(list)
    matching = route_segments.combine(route_stop_segments, lambda routeS, stopS: 1 if set(routeS) >= set(stopS) else 0)
    print(matching[matching==0])
    print(matching.sum(), len(matching))
    # TODO: 126 139
    assert(matching.sum() == len(matching))
    print('All stop segment present in route segments')


def test_stops():
    bus_stops = pd.read_csv(databaseFolder + 'bus_stop.csv')
    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_stops.csv')
    print(len(pt_bus_stops.stop_code.unique()), len(bus_stops.id.unique()))
    assert(len(bus_stops) == len(bus_stops.id.unique()))


def test_a_route():
    pt_bus_routes = pd.read_csv(databaseFolder + 'pt_bus_routes.csv')
    bus_stops = pd.read_csv(databaseFolder + 'bus_stop.csv')
    pt_bus_stops = pd.read_csv(databaseFolder + 'pt_bus_stops.csv')

    pt_bus_stops = pt_bus_stops.merge(bus_stops, left_on='stop_code', right_on='id', how='left')

    route_segments = pt_bus_routes.groupby('route_id')['section_id'].apply(list)
    route_stop_segments = pt_bus_stops.groupby('route_id')['section_id'].apply(list)
    print(pt_bus_stops[pt_bus_stops.section_id == 4761])
    print(bus_stops[bus_stops.id == 3829])
    print(route_segments['BL_77_1'])
    print(route_stop_segments['BL_77_1'])


test_route_segment_connectivity()
test_busstop_consistency()
test_route_consistency()
test_stops()
