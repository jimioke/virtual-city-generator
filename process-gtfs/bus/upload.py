import psycopg2,pdb
# FOLDER = 'Outputs/Baltimore_auto_sprawl2/simmobility/'
FOLDER = 'to_db_complete/'
# FOLDER = 'to_db_pruned_bus_tables/'

# tables = ['age_category','education','employment_sector','gender','income_category']
tables = [
'bus_stop',
# 'bus_stop_wgs84',
# 'bus_stop_original_coords',
# 'pt_bus_routes',
# 'pt_bus_stops',
# 'pt_bus_dispatch_freq'
]

# tables = [
# 'pt_train_route',
# 'pt_train_route_platform',
# 'train_platform',
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
