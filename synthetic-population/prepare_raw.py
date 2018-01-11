import pandas as pd

# Prepare households
# with open('usa_00001.csv','r') as f:
#     for i in range(4):
#         print(next(f))
#     # head = [next(f) for x in range(5)]
# # print(head)
# marginal_files = ['ACS_15_5YR_B08202.csv','ACS_15_5YR_B08203.csv','ACS_15_5YR_B11016.csv','ACS_15_5YR_B19001.csv']


# files names
# sex_age = 'ACS_15_5YR_B01001.csv'
# hsize_veh = 'ACS_15_5YR_B08201.csv'
# workers_veh = 'ACS_15_5YR_B08203.csv'
# htype_hsize = 'ACS_15_5YR_B11016.csv'
# vw, vf, vn, wf, wn, fn = []

# df = pd.read_csv('../data-input/marginals_2d.csv')

# group_vehicles = {
# 0:73165,
# 1:93749,
# 2:55933,
# 3:12005,
# 4:3548
# }

# "YEAR","DATANUM","SERIAL","HHWT","REGION","COUNTY","MET2013","CITYPOP","PUMA","CPUMA0010","GQ","OWNERSHP","OWNERSHPD","HHINCOME","UNITSSTR","PERNUM","PERWT","FAMSIZE","RELATE","RELATED","SEX","AGE","MARST","BIRTHYR","SCHOOL","EDUC","EDUCD","EMPSTAT","EMPSTATD","LABFORCE","OCC","INCTOT","FTOTINC","TRANWORK","TRANTIME"

# COUNTY = 24510
# FAMSIZE = people per household
# sex =
# age =
# ownershp=?

# df = pd.read_csv('usa_00002.csv')
# # df.loc[df['COUNTY'] == 24510]]
# # print(df.COUNTY)
# # print(df[df.iloc[:,1].map(lambda x: type(x) == str)])
# print(df.dtypes)
# # df = df.where(df['COUNTY'] == 24510)
# df = df[df.COUNTY == 24510]
# # df = df[['FAMSIZE','SEX', 'AGE', 'OWNERSHP']]
# df.to_csv("Balt.csv")

# import csv
# f = open('../data-input/hh_marginals_2d.csv')
numLines = 0
fromFile = open('usa_00003.csv', 'r')
toFile = open('Baltimore_sample.csv', 'w')
# header
header = next(fromFile)
print(len(header.split(",")), header.split(",")[6] )
toFile.write(header)

# Balt_county 24005
# balt city 24510
line = next(fromFile)
codeSet = set()
while line:
    code = line.split(",")[6]
    codeSet.add(code)
    if code == "24005":
        toFile.write(line)
    numLines +=1
    line = fromFile.readline()
print("num of samples", numLines)
print("codes: ", codeSet )
fromFile.close()
toFile.close()

# csv_f = csv.reader(f)
# for row in csv_f:
#     print(row)
#
# import chardet
#
# with open('filename.csv', 'rb') as f:
#     result = chardet.detect(f.read())  # or readline if the file is large
#
#
# pd.read_csv('filename.csv', encoding=result['encoding'])
# print(df.head(3))

# with open('../data-input/hh_marginals_2d.csv','r') as fileMarg:
#
#     df = pd.DataFrame(l.rstrip().split() for l in fileMarg)
#
#     print(df.head(4))
    # for l in range(4):
    #     print(next(fileMarg))
    # fileMarg





# content = f.readlines()
# next(f) # skip first row
# df = pd.DataFrame(l.rstrip().split() for l in f)
#
# print(df.head(4))


# Sample: GroupId, IndId, # of ind in group, # vehicles, # workers, # householdtype, sex, age
# Individual: sex, age, education,  worker, # vehicle,
# Household: # vehicles, # workers, householdtype,

##### Household fields:
# vehicles: 0,1,2,3,4 or more
# workers: 0,1,2,3 or more
# familytype: 0,1 (Nonfamily, family)
# number of members: 0,1,2,3,4,5,6.

##### Individual fields
# sex: 0, 1 (female 0, male 1)
# age: 0,1,2...17
# education: 0,1,2,..11
# work: 0,1
# vehicle: 0, 1
