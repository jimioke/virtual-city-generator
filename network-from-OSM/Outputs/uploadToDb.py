import psycopg2,pdb

tables = ['node','link_polyline','link','segment_polyline','segment','lane_polyline','lane']
tables.extend(['connector','turning_path_polyline','turning_path','turning_group','link_default_travel_time'])
tables = ['supply.'+item for item in tables]
filenames = ['node-nodes.csv','link-nodes.csv','link-attributes.csv','segment-nodes.csv','segment-attributes.csv']
filenames.extend(['lane-nodes.csv','lane-attributes.csv','connector.csv','turning-nodes.csv','turning-attributes.csv','turninggroups.csv','linkttsdefault.csv'])



# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect("host='18.58.5.170' port='5432' dbname='protocity1' user='postgres' password='ITSLab2016!'")

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
