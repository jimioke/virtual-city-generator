import psycopg2,pdb
# FOLDER = 'Outputs/Baltimore_auto_sprawl2/simmobility/'
FOLDER = 'Outputs/to_db/'

# tables = ['age_category','education','employment_sector','gender','income_category']
tables = [
'mrt_line_properties',
'mrt_stop',
'pt_opposite_lines',
'pt_train_block_polyline',
'pt_train_block',
'pt_train_dispatch_freq',
'pt_train_platform_transfer_time',
'pt_train_route_platform',
'pt_train_route',
'train_access_segment',
'train_fleet',
'train_platform',
'train_uturn_platforms',
# 'train_transit_edge',
'train_stop',
'mrt_stop_wgs84',
'rail_transit_edge'
]

# tables = [
# # 'pt_train_route',
# # 'pt_train_route_platform',
# # 'train_platform',
# 'mrt_stop_wgs84',
# # 'rail_transit_edge'
# ]
filenames = [ FOLDER + f+'.csv' for f in tables]
tables = ['supply.' + item for item in tables]


# get a connection, if a connect cannot be made an exception will be raised here
# conn = psycopg2.connect("host='18.58.5.170' port='5432' dbname='auto_sprawl' user='postgres' password='ITSLab2016!'")
conn = psycopg2.connect("host='18.58.5.170' port='5432' dbname='auto_sprawl' user='postgres' password='ITSLab2016!'")
# conn.cursor will return a cursor object, you can use this cursor to perform queries
cursor = conn.cursor()
print "Connected!"

for i in xrange(len(tables)):
    tab,fname = tables[i],filenames[i]
    #chk_sql = """SET FOREIGN_KEY_CHECKS = 0;"""
    #cursor.execute(chk_sql)
    del_sql = """TRUNCATE TABLE """+tab+""" CASCADE;"""
    cursor.execute(del_sql)
    copy_sql = """COPY """ + tab + """ FROM stdin WITH CSV HEADER DELIMITER as ',' """
    with open(fname, 'r') as ifile:
        cursor.copy_expert(sql=copy_sql,file=ifile)
    print "Uploaded file " + fname + " to TABLE "+tab
    #pdb.set_trace()
conn.commit()
conn.close()
