
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
	# Specify all variable names that is related
	df = df[df['PUMA'].isin(map(int,pumaInArea))][['SERIALNO','SPORDER','PUMA','AGEP',
	'COW','JWMNP','JWTR','MAR','RELP','SEX','SCHL','ESR','PINCP','ADJINC']]
	print df.shape
	df.to_csv('data/ss15ptx_clean.csv', index = False)

	return df





def preprocessingMarginal():
	pass

dirname = 'data'
hhfilename = 'ss15htx.csv'
psfilename = 'ss15ptx.csv'
map_filename = '2010_Census_Tract_to_2010_PUMA.txt'


# Give all the counties in A specific metro area
# Here we are in Texas (48), Houston metro area
stateID = '48'
countyInArea = ['015','039','071','157','167','201','291','339','473']
# Read the map file
mapCTtoPUMA = pd.read_csv(os.path.join(dirname,map_filename),sep = ',',converters={'STATEFP':str,'COUNTYFP':str,'PUMA5CE':str})


# Get PUMA which is in Houston metro area
pumaInArea = mapCTtoPUMA[mapCTtoPUMA['STATEFP']==stateID]
pumaInArea = pumaInArea[pumaInArea['COUNTYFP'].isin(countyInArea)]['PUMA5CE'].unique()
print pumaInArea




#household = pd.read_csv(os.path.join(dirname,hhfilename))
# Write a subset of the whole data, easier to open in excel
#household[0:500].to_csv(os.path.join(dirname,'sample_'+hhfilename),index = False)

person = preprocessingPersonPUMS(dirname, psfilename, pumaInArea)
#person[0:500].to_csv(os.path.join(dirname, 'sample_'+psfilename), index = False)

