import psycopg2,pdb

FOLDER = 'to_db/'

tables = [
'parking',
'taxi_fleet',
'taxi_stand'
]
filenames = [ FOLDER + f+'.csv' for f in tables]
tables = ['supply.'+item for item in tables]


# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect("host='18.58.0.111' port='5432' dbname='???' user='postgres' password='ITSLab2016!'")

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
