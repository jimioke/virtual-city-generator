
import pandas as pd 
import numpy as np
import os
import ipfn
from categorize import *
from marginal_processing import *
from datetime import datetime


def selectPersonPUMS(dirname,filename,pumaInArea):
	'''
	delete unnecessary columns

	df: Data Frame - original PUMS data
	pumaInArea: list - all related puma
	'''

	df = pd.read_csv(os.path.join(dirname,filename))
	print df.shape
	# Specify all person variable names that is related
	df = df[df['PUMA'].isin(map(int,pumaInArea))][['SERIALNO','SPORDER','PUMA','AGEP',
	'COW','JWMNP','JWTR','MAR','RELP','SEX','SCHL','ESR','PINCP','ADJINC']]
	print df.shape
	df.to_csv('data/ss15ptx_clean.csv', index = False)



def preprocessingHouseholdPUMS(dirname, filename, pumaInArea):
	
	df = pd.read_csv(os.path.join(dirname, filename))
	print df.shape
	# Specify all household variable names that is related
	df = df[df['PUMA'].isin(map(int,pumaInArea))][['SERIALNO','PUMA','NP','VEH','HHT',
	'HINCP','HUPAC','WIF']]
	print df.shape
	df.to_csv('data/ss15htx_clean.csv', index = False)

	return df


def getMarginal(dirname, filename, relevantSubjects):

	'''
	relevantSubjects specify names of variables we need
	marginalDF is MultiIndex pandas DataFrame

	'''

	marginal = dict()
	rawTable = pd.read_csv(os.path.join(dirname,filename), skiprows = [0])

	# delete all columns which is just Margin of Error, and delete Female&Male subcategory
	colNameToDrop = [cname for cname in rawTable.columns if cname.find('Margin of Error')>-1]
	rawTable.drop(colNameToDrop,1,inplace = True)
	colNameToDrop = [cname for cname in rawTable.columns[3:] if not cname.split(';')[0]=='Total']
	rawTable.drop(colNameToDrop,1,inplace = True)

	nrow, ncol = rawTable.shape

	for i in range(nrow):
		subjects = []
		rownames = []
		numbers = []
		county = rawTable['Geography'][i]
		for j in range(3,ncol):
			if rawTable.columns[j].split(';')[-1].split('-')[0].split('(')[0].strip() in relevantSubjects:
				cname = rawTable.columns[j].split(';')[-1]
				subjects.append(cname.split('-')[0].split('(')[0].strip())
				rownames.append(cname.split('-')[-1].strip())
				numbers.append(rawTable.iloc[i,j])
		arrays = [subjects,rownames]
		marginal[county] = pd.Series(numbers, index = arrays, name = county)
	
	marginalDF = pd.concat([marginal[county] for county in marginal.keys()], axis = 1)
	return marginalDF
	


def getCountyId_and_Name(dirname, filename):

	df = pd.read_csv(os.path.join(dirname, filename),dtype={'Id2': str},skiprows = [0])
	countyTable = pd.DataFrame()
	countyTable['name'] = df['Geography']
	countyTable['id'] = df['Id2'].str[2:]

	return countyTable 




def getMarginalS0101(dirname, filename):
	'''
	construct a dict object 'marginal' whose keys are the names of counties in the area
	within each county, the marginal distribution for variables are recorded

	marginal: dictionary - keys are county names
	marginal[County]: MultiIndex pandas Series

	'''


	marginal = dict()
	rawTable = pd.read_csv(os.path.join(dirname,filename), skiprows = [0])

	# delete all columns which is just Margin of Error, and delete Female&Male subcategory
	colNameToDrop = [cname for cname in rawTable.columns if cname.find('Margin of Error')>-1]
	rawTable.drop(colNameToDrop,1,inplace = True)

	# drop subjects in rawTable that's not relevant ot us
	subjectsToDrop = ['SELECTED AGE CATEGORIES','SUMMARY INDICATORS','PERCENT IMPUTED']
	for subject in subjectsToDrop:
		rawTable.drop([name for name in rawTable.columns if name.find(subject)>-1],1,inplace = True)

	nrow, ncol = rawTable.shape

	# reformat one line in rawTable into a table
	# the iteration of columns starts at 3! 
	
	for i in range(nrow):
		
		subjects = []
		rownames = []
		numbers = []
		county = rawTable['Geography'][i]
		for j in range(3, ncol):
			cname = rawTable.columns[j]
			v1 = cname.split(';')[0]
			v2 = cname.split(';')[2].strip()
			v3 = v2.split('-')[0]
			if v2 == 'Total population':
				subjects.append(v3)
				rownames.append(v1)
				numbers.append(rawTable.iloc[i,j])
			elif v1 == 'Total':
				print v2
				subjects.append(v3)
				rownames.append(v2.split('-')[1])
				numbers.append(rawTable.iloc[i,j])
		print subjects, rownames, numbers
		arrays = [np.array(subjects), np.array(rownames)]
		marginal[county] = pd.Series(numbers,index = arrays)
	
	return marginal
		



dirname = 'data'
out_dir = 'data_output'
hhfilename = 'ss15htx.csv'
psfilename = 'ss15ptx.csv'
map_filename = '2010_Census_Tract_to_2010_PUMA.txt'

marginal_filenames = ['ACS_15_5YR_S0101.csv','ACS_15_5YR_S0601.csv','ACS_15_5YR_S0801.csv']


# Give all the counties in A specific metro area
# Here we are in Texas (48), Houston metro area
stateID = '48'
countyTable = getCountyId_and_Name(dirname, marginal_filenames[1])
countyInArea = countyTable['id']


# Read the file which map census tract to puma and conty
mapCTtoPUMA = pd.read_csv(os.path.join(dirname,map_filename),sep = ',',converters={'STATEFP':str,'COUNTYFP':str,'PUMA5CE':str})
# select puma which is in Houston metro area
mapCTtoPUMA = mapCTtoPUMA[mapCTtoPUMA['STATEFP']==stateID]
mapCTtoPUMA = mapCTtoPUMA[mapCTtoPUMA['COUNTYFP'].isin(countyInArea)] 
# Get PUMA which is in Houston metro area
pumaInArea = mapCTtoPUMA['PUMA5CE'].unique()




#########################  Marginal Distribution #########################
#marginal = getMarginalS0101(dirname, marginal_filenames[0])

# TODO:  write "get marginal distribution" into a function
# add new categories to variables that only apply to people over 15

# Get marginals from file S0601
relevantSubjectsS0601 = ['Total population','AGE','SEX','MARITAL STATUS','EDUCATIONAL ATTAINMENT',
	'INDIVIDUALS\' INCOME IN THE PAST 12 MONTHS']
marginalDF1 = getMarginal(dirname, marginal_filenames[1], relevantSubjectsS0601)

# Get marginals from file S0801
relevantSubjectsS0801 = ['VEHICLES AVAILABLE']
marginalDF2 = getMarginal(dirname, marginal_filenames[2], relevantSubjectsS0801)

# Concatenate marginal dafaframes from different files
marginalDF = pd.concat([marginalDF1,marginalDF2])
marginalDF.to_csv('person_marginals.csv')


#########################       Sample Data      #########################



# household = preprocessingHouseholdPUMS(dirname, hhfilename, pumaInArea)
# Write a subset of the whole data, easier to open in excel
# household[0:500].to_csv(os.path.join(dirname, 'sample_'+hhfilename), index = False)


#selectPersonPUMS(dirname, psfilename, pumaInArea)
#Write a subset of the PUMS person data
#person[0:500].to_csv(os.path.join(dirname, 'sample_'+psfilename), index = False)
psfilename = 'ss15ptx_clean.csv'
person, categories = categorizePersonPUMS(dirname, psfilename)




####################################################################################

# HOUSEHLD MARGINAL DATA


hh_marginal_files = ['ACS_15_5YR_B08202.csv','ACS_15_5YR_B08203.csv','ACS_15_5YR_B11016.csv','ACS_15_5YR_B19001.csv'] 
one_marginal, two_marginal = main_marginal_process(dirname, hh_marginal_files)
# write marginal distributions

# HOUSEHOLD PUMS DATA
hh_sample_categorized = categorizeHhPUMS('data','ss15htx_clean.csv')
subjects = hh_sample_categorized.columns[2:]

hh_joint_dist = getHhJointDist(hh_sample_categorized, one_marginal, two_marginal, mapCTtoPUMA, countyTable)


# ipf
# ipf

for county in one_marginal.keys():
	#print one_marginal[county]
	time1 = datetime.now()
	ipf_result = getIPFresult_for_county(one_marginal[county],two_marginal[county], hh_joint_dist[county])
	print datetime.now()-time1
	#print ipf_result
	jd = hh_joint_dist[county].rename('sample').reset_index()
	jd_and_ipf = pd.merge(jd,ipf_result, on=list(subjects))
	jd_and_ipf.to_csv(os.path.join(out_dir, county+'ipf_result.csv'))



#########################  Iterative Proportional Fitting  #########################


#result = setup_IPF_for_county(person, marginalDF, countyTable, mapCTtoPUMA, categories)



