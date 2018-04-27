import psycopg2,pdb
# FOLDER = 'Outputs/Baltimore_auto_sprawl2/simmobility/'
FOLDER = 'to_db/'

# tables = ['age_category','education','employment_sector','gender','income_category']
tables = [
# 'land_use_type',
# 'land_use_zone',
# 'taz',
# 'education',
# 'employment_status',
# 'age_category',
# 'gender',
'individual_with_income',
# 'household',
# 'sla_address_id',
# 'vehicle_ownership_option_id'
]
filenames = [ FOLDER + f+'.csv' for f in tables]
tables = ['synpop12.'+item for item in tables]
tables = ['synpop12.individual_with_income']

# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect("host='18.58.5.170' port='5432' dbname='auto_sprawl' user='postgres' password='ITSLab2016!'")

# conn.cursor will return a cursor object, you can use this cursor to perform queries
cursor = conn.cursor()
print "Connected!"

for i in xrange(len(tables)):
    tab,fname = tables[i],filenames[i]
    #chk_sql = """SET FOREIGN_KEY_CHECKS = 0;"""
    #cursor.execute(chk_sql)
    # del_sql = """TRUNCATE TABLE """+tab+""" CASCADE;"""
    # cursor.execute(del_sql)
    copy_sql = """COPY """ + tab + """ FROM stdin WITH CSV HEADER DELIMITER as ',' """
    with open(fname, 'r') as ifile:
        cursor.copy_expert(sql=copy_sql,file=ifile)
    print "Uploaded file " + fname + " to TABLE "+tab
    #pdb.set_trace()
conn.commit()
conn.close()
