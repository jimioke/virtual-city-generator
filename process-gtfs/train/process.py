################################################################################
# Description: create SimMobility tables.
# Written by: Iveel Tsogsuren
################################################################################
import pandas as pd
from shapely.geometry import Point, LineString
import geopandas as gpd
from collections import defaultdict
from shapely.ops import transform
from functools import partial
import pyproj
from shapely.ops import split
from process_helper import*

processFolder='Outputs/Process/'
outputFolder='Outputs/to_db_may15/'

train_stop_cols = ['shape_id', 'x', 'y', 'z', 'platform_name', 'station_name', 'type','op_year']
train_access_segment_cols = ['mrt_stop_id', 'segment_id']
train_platform_cols = ['platform_no', 'station_no', 'line_id', 'capacity', 'type', 'block_id', 'pos_offset', 'length']
pt_train_block_cols = ['block_id', 'default_speed_limit', 'accelerate_rate', 'decelerate_rate', 'length']
pt_train_block_polyline_cols = ['polyline_id', 'x', 'y', 'z', 'sequence_no']
pt_train_dispatch_freq_cols = ['frequency_id', 'line_id', 'start_time', 'end_time', 'headway_sec']
pt_train_route_platform_cols = ['line_id', 'platform_no', 'sequence_no']
pt_train_route_cols = ['line_id', 'block_id', 'sequence_no']
pt_train_platform_transfer_time_cols = ['station_no', 'platform_first', 'platform_second', 'transfered_time_sec']
pt_opposite_lines_cols = ['line', 'opp_line']
dispatch_detialed_cols = ['trip_id','arrival_time','departure_time','stop_id','stop_sequence','service','service_id','stop_lat','stop_long','C_type']

# Selected shapes
# Manually select routes: opposite shapes
Route_to_shapes = {
10196: ['L5', 'L1'],
10210: ['L16', 'L23'],
10222: ['L51', 'L40'],
10223: ['L89', 'L75'],
10224: ['L153', 'L143'],
}

# line (name up to you), direction (opposite pairs), opp_direction (2,1)
Line_pair = namedtuple('Line_pair', 'line direction opp_direction')
LinePairs = {
'L5': Line_pair(line='A', direction=1, opp_direction=2),
'L1': Line_pair(line='A', direction=2, opp_direction=1),
'L16': Line_pair(line='B', direction=1, opp_direction=2),
'L23': Line_pair(line='B', direction=2, opp_direction=1),
'L51': Line_pair(line='C', direction=1, opp_direction=2),
'L40': Line_pair(line='C', direction=2, opp_direction=1),
'L89': Line_pair(line='D', direction=1, opp_direction=2),
'L75': Line_pair(line='D', direction=2, opp_direction=1),
'L153': Line_pair(line='F', direction=1, opp_direction=2),
'L143': Line_pair(line='F', direction=2, opp_direction=1),
}

# Expect each shape is a unique line (one direcion) and must pair up with other shape.
route_df, shape, stops_df, stoptime_df, trip_df = get_gtfs(inFolder='Outputs/clean_gtfs/')
# trip, linetime, line_toStartTimes
trip_wLine, stoptime_df, line_stoptime, line_toStartTimes = createLinesPlatformName(stoptime_df, stops_df, trip_df, route_df, shape, LinePairs)
train_route_platform, train_route, train_block, train_block_polyline, line_stoptime = createBlocks(line_stoptime, shape)
train_stop, train_platform, line_stoptime = platform_stations(line_stoptime, stops_df)
dispatch_freq_table, dispatch_detialed = dispatch_freq(line_stoptime, line_toStartTimes)
#
transfer_time = transfer_time(train_platform)
opposite_lines = line_stoptime.drop_duplicates(subset=['line_id'])
opposite_lines = opposite_lines.rename(columns={'line_id':'line'})[['line', 'opp_line']]
train_uturn_platforms = create_uturn(train_route, train_platform)
mrt_line_properties = mrt_line_properties(train_route)
train_fleet = train_fleet(train_route)
train_transit_edge = transit_edge(dispatch_detialed)

train_uturn_platforms.to_csv(outputFolder + 'train_uturn_platforms.csv', index=False)
mrt_line_properties.to_csv(outputFolder + 'mrt_line_properties.csv', index=False)
train_fleet.to_csv(outputFolder + 'train_fleet.csv', index=False)
train_transit_edge.to_csv(outputFolder + 'train_transit_edge.csv', index=False)

line_stoptime.to_csv(outputFolder + 'line_stoptime.csv', index=False)
transfer_time.to_csv(outputFolder + 'pt_train_platform_transfer_time.csv', index=False)
train_stop.to_csv(outputFolder + 'mrt_stop.csv', index=False)
train_platform[train_platform_cols].to_csv(outputFolder + 'train_platform.csv', index=False)
train_block.to_csv(outputFolder + 'pt_train_block.csv', index=False)
train_block_polyline.to_csv(outputFolder + 'pt_train_block_polyline.csv', index=False)
train_route_platform[pt_train_route_platform_cols].to_csv(outputFolder + 'pt_train_route_platform.csv', index=False)
train_route[pt_train_route_cols].to_csv(outputFolder + 'pt_train_route.csv', index=False)
opposite_lines.to_csv(outputFolder + 'pt_opposite_lines.csv', index=False)
dispatch_freq_table.to_csv(outputFolder + 'pt_train_dispatch_freq.csv', index=False)
dispatch_detialed[dispatch_detialed_cols].to_csv(outputFolder + 'weekday_train_seq_31Mar18.csv', index=False)

#
# # Use when we want use created tables.
# # line_stoptime = pd.read_csv(outputFolder + 'line_stoptime.csv')
# # train_stop = pd.read_csv(outputFolder + 'pt_train_stop.csv')
# # train_platform = pd.read_csv(outputFolder + 'pt_train_platform.csv')
# # train_block = pd.read_csv(outputFolder + 'pt_train_block.csv')
# # train_block_polyline = pd.read_csv(outputFolder + 'pt_train_block_polylines.csv')
# # train_route_platform = pd.read_csv(outputFolder + 'train_route_platform.csv')
# # train_route = pd.read_csv(outputFolder + 'train_route.csv')
#

print('Convert segments -------------------------------------')
convertSegment(simFolder='Auto_sprawl_drive_main/SimMobility/')
access_segment = find_access_segment(train_stop, simFolder='Auto_sprawl_drive_main/simmobility/')
access_segment.to_csv(outputFolder + 'train_access_segment.csv', index=False)
#
# # We need train stops in lat and long for public transit graph generation.
convertCoordinates()
