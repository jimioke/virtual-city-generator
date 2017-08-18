
import pandas as pd 
import os
import ipfn


def preprocessingPersonPUMS(dirname,filename,pumaInArea):
	'''
	delete unnecessary columns
	and aggregate variables like age into categories

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

	return df


def preprocessingHouseholdPUMS(dirname, filename, pumaInArea):
	
	df = pd.read_csv(os.path.join(dirname, filename))
	print df.shape
	# Specify all household variable names that is related
	df = df[df['PUMA'].isin(map(int,pumaInArea))][['SERIALNO','PUMA','NP','VEH','HHT',
	'HINCP','HUPAC','WIF']]
	print df.shape
	df.to_csv('data/ss15htx_clean.csv', index = False)

	return df



def preprocessingMarginal(dirname, marginal_filename):
	'''
	construct a dict object 'marginal' whose keys are the names of counties in the area
	within each county, the marginal distribution for variables are recorded

	marginal: dictionary - keys are county names
	marginal[Countyi]: dictionary - keys are names of variables

	'''
	
	rawTable = pd.read_csv(os.path.join(dirname,marginal_filename))
	
	print range(rawTable.shape[0])
	print rawTable.columns[1:10]

	# delete all columns which is just Margin of Error
	colNameToDrop = [cname for cname in rawTable.columns if cname.find('Margin of Error')>-1]
	rawTable.drop(colNameToDrop,1,inplace = True)

	# drop subjects in rawTable that's not relevant ot us
	subjectsToDrop = ['SELECTED AGE CATEGORIES','SUMMARY INDICATORS','PERCENT IMPUTED']
	for subject in subjectsToDrop:
		rawTable.drop([name for name in rawTable.columns if name.find(subject)>-1],1,inplace = True)


	marginal = dict()
	nrow = rawTable.shape[0]
	ncol = rawTable.shape[1]

	df = pd.DataFrame()
	vNameList = ['AGE']
	# reformat one line in rawTable into a table
	for i in range(3, ncol):
		cname = rawTable.columns[i]
		v1 = cname.split(';')[0]
		v2 = cname.split(';')[2]
		df.set_value(v2,v1,rawTable.iloc[0,i])
		
	print df




	#for i in range(nrow):
	#	marginal[rawTable['Geography'][i]] = dict()
		
	#	rawTable['Total'][3]





dirname = 'data'
hhfilename = 'ss15htx.csv'
psfilename = 'ss15ptx.csv'
map_filename = '2010_Census_Tract_to_2010_PUMA.txt'

marginal_filename = 'ACS_15_5YR_S0101.csv'


# Give all the counties in A specific metro area
# Here we are in Texas (48), Houston metro area
stateID = '48'
countyInArea = ['015','039','071','157','167','201','291','339','473']
# Read the map file
mapCTtoPUMA = pd.read_csv(os.path.join(dirname,map_filename),sep = ',',converters={'STATEFP':str,'COUNTYFP':str,'PUMA5CE':str})


# Get PUMA which is in Houston metro area
pumaInArea = mapCTtoPUMA[mapCTtoPUMA['STATEFP']==stateID]
pumaInArea = pumaInArea[pumaInArea['COUNTYFP'].isin(countyInArea)]['PUMA5CE'].unique()
#print pumaInArea





preprocessingMarginal(dirname, marginal_filename)



# household = preprocessingHouseholdPUMS(dirname, hhfilename, pumaInArea)
# Write a subset of the whole data, easier to open in excel
# household[0:500].to_csv(os.path.join(dirname, 'sample_'+hhfilename), index = False)

#person = preprocessingPersonPUMS(dirname, psfilename, pumaInArea)
#person[0:500].to_csv(os.path.join(dirname, 'sample_'+psfilename), index = False)

