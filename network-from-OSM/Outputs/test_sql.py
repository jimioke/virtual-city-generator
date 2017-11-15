import psycopg2,pdb
# from mysql.connector import MySQLConnection, Error
# from python_mysql_dbconfig import read_db_config

# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect("host='18.58.5.170' port='5432' dbname='protocity1' user='postgres' password='ITSLab2016!'")

# conn.cursor will return a cursor object, you can use this cursor to perform queries
cursor = conn.cursor()
# print "Connected!"
#
# cursor.execute('exec get_taxi_fleet_on_call(00:00:00, 00:03:00)')
#
# rc = cursor.fetchval()

# args = ['00:00:00', '00:05:00']
args = []
result_args = cursor.callproc('get_road_segments', args)
# result_args = cursor.callproc('get_nodes', args)

data = cursor.fetchall()
print(data)

# print(result_args)
#
# for result in cursor.stored_results():
#     print result.fetchall()
cursor.close()
