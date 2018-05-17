import pandas as pd
import psycopg2,pdb
import pandas.io.sql as psql

outputFolder = '31Mar18/'

# 1. P_nodes_.csv (roadnetwork nodes)
# "select concat('N_', id) as stop_id, concat('N_', id) as stop_code, concat('N_', id) as stop_name, x as stop_lat, y as stop_lon, concat('N_', id) as 'EZLink_Name', 0 as 'stopType' from supply.node_wgs84;"
# from node_wgs84:
#
# 2. SimM_bus_stops_.csv
# "select code as stop_id, code as stop_code, name as stop_name, x as stop_lat, y as stop_lon, code as 'EZLink_Name', 1 as 'Type', 1 as 'stopType' from supply.bus_stop_wgs84 where status = 'OP';"
# from bus_stop_wgs84: ['x', 'y', 'z', 'id', 'code', 'section_id', 'name', 'status', 'terminal', 'length', 'section_offset', 'tags', 'reverse_section', 'terminal_node']
#
# 3. bus_journeytime_.csv
# service_id,trip_id,stop_id,stop_sequence,arrival_time,departure_time,dwelling_time
#
# 4. SimM_RTS_stops_.csv
# "select platform_name as stop_id, platform_name as stop_code, station_name as stop_name, x as stop_lat, y as stop_lon, concat('STN ', station_name) as 'EZLink_Name', 2 as 'Type', 2 as 'stopType' from supply.mrt_stop_wgs84;"
# from mrt_stop_wgs84:  ['shape_id', 'x', 'y', 'z', 'id', 'platform_name', 'station_name', 'type', 'op_year']
# "stop_id";"stop_code";"stop_name";"stop_lat";"stop_lon";"EZLink_Name";"Type";"stopType"
#
# 5. weekday_train_seq_.csv
# trip_id,arrival_time,departure_time,stop_id,stop_sequence,service,service_id,stop_lat,stop_long,C_type

# change x - lont, y - lat
mrt_stops_query = """select platform_name as stop_id, platform_name as stop_code, station_name as stop_name, y as stop_lat, x as stop_lon, concat('STN_', station_name) as "EZLink_Name", 2 as "Type", 2 as "stopType"  from supply.mrt_stop_wgs84;"""
# select code as stop_id, code as stop_code, name as stop_name, x as stop_lat, y as stop_lon, code as "EZLink_Name", 1 as "Type", 1 as "stopType" from supply.bus_stop_wgs84 where status = 'OP';
bus_stop_query = """select code as stop_id, code as stop_code, name as stop_name, y as stop_lat, x as stop_lon, code as "EZLink_Name", 1 as "Type", 1 as "stopType" from supply.bus_stop_wgs84 where status = 'OP';"""
# select concat('N_', id) as stop_id, concat('N_', id) as stop_code, concat('N_', id) as stop_name, x as stop_lat, y as stop_lon, concat('N_', id) as "EZLink_Name", 0 as "stopType" from supply.node_wgs84;
node_query = """select concat('N_', id) as stop_id, concat('N_', id) as stop_code, concat('N_', id) as stop_name, y as stop_lat, x as stop_lon, concat('N_', id) as "EZLink_Name", 0 as "Type", 0 as "stopType" from supply.node_wgs84;"""

stop_columns = ['stop_id','stop_code','stop_name','stop_lat','stop_lon','EZLink_Name','Type','stopType']
stop_columns = dict(zip(list(range(8)), stop_columns))
def write(cursor, query, columns, outFile):
    resoverall = cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall())
    print(df.columns)
    df.rename(columns=columns, inplace=True)
    df.to_csv(outFile, index=False)

# def write(conn, cursor, query, columns, outFile):
#     # resoverall = cursor.execute(query)
#     # feched = cursor.fetchall()
#     # # df = pd.DataFrame(cursor.fetchall())
#     df= psql.frame_query(query, conn, columns=columns)
#     print(df.columns)
#     df.to_csv(outFile, index=False)

def get_from_db():
    conn = psycopg2.connect("host='18.58.0.111' port='5432' dbname='auto_sprawl' user='postgres' password='ITSLab2016!'")
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    print("Connected!")
    write(cursor, mrt_stops_query, stop_columns, outputFolder + 'SimM_RTS_stops_31Mar18.csv')
    print(bus_stop_query)
    write(cursor, bus_stop_query, stop_columns, outputFolder + 'SimM_bus_stops_31Mar18.csv')
    write(cursor, node_query, stop_columns, outputFolder + 'P_nodes_31Mar18.csv')
    print("Done")
    conn.commit()
    conn.close()

# get_from_db()

def testFiles(inFolder='31Mar18/'):
    bus_journeytime = pd.read_csv(inFolder + 'bus_journeytime_31Mar18.csv')
    nodes = pd.read_csv(inFolder + 'P_nodes_31Mar18.csv')
    bus_stops = pd.read_csv(inFolder + 'SimM_bus_stops_31Mar18.csv')
    rt_stops = pd.read_csv(inFolder + 'SimM_RTS_stops_31Mar18.csv')
    weekday = pd.read_csv(inFolder + 'weekday_train_seq_31Mar18.csv')
    print(bus_journeytime.isnull().sum())
    print(nodes.isnull().sum())
    print(bus_stops.isnull().sum())
    print(rt_stops.isnull().sum())
    print(weekday.isnull().sum())
# testFiles()
