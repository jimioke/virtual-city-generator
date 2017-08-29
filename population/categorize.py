
import pandas as pd 
import numpy as np 
import os
import math

def categorizePersonPUMS(dirname, psfilename):
	'''
	replace values of each variable in sample data with categories from aggregate data

	'''

	df = pd.read_csv(os.path.join(dirname, psfilename))
	selectColumns = ['SERIALNO','SPORDER','PUMA','SEX','AGEP','MAR','SCHL','PINCP']
	df = df[selectColumns]
	df.columns.values[3:] = ['sex','age','mar','edu','inc']
	print max(df['age'])
	print min(df['inc']), max(df['inc'])

	sexC = {
			'Male': [1],
			'Female': [2]
			}

	ageC = {
			'Under 5 years': range(0,5),
			'5 to 17 years': range(5,18),
			'18 to 24 years': range(18,25),
			'25 to 44 years': range(25,45),
			'45 to 54 years': range(45,55),
			'55 to 64 years': range(55,65),
			'65 to 74 years': range(65,75),
			'75 years and over': range(75,125)
			}
	marC = {
			'Never married': [5],
			'Married': [1],
			'Divorced or separated': [3,4],
			'Widowed': [2]
			}

	eduC = {
			'Less than high school graduate': range(1,16),
			'High school graduate': [16,17],
			'Some college or associate\'s degree': range(18,21),
			'Bachelor\'s degree': [21],
			'Graduate or professional degree': range(22,25),
			}

	incC = {
			'$1 to $9,999 or loss': [min(min(df['inc']),1), 9999],
			'$10,000 to $14,999': [10000,14999],
			'$15,000 to $24,999': [15000,24999],
			'$25,000 to $34,999': [25000,34999],
			'$35,000 to $49,999': [35000,49999],
			'$50,000 to $64,999': [50000,64999],
			'$65,000 to $74,999': [65000,74999],
			'$75,000 or more': [75000, max(max(df['inc']),80000)],
			}



	categories = {'sex': sexC, 'age': ageC, 'mar': marC, 'edu': eduC, 'inc': incC}
	newdf = df.copy()
	# processing sex, age, marriage status
	for sub in ['sex','age','mar']:
		for cat in categories[sub].keys():
			newdf[sub] = newdf[sub].replace(categories[sub][cat],cat)

	# categorize education attainment and income

	newdf.loc[df['age'] < 25,'edu'] = 'Less than 25'
	newdf.loc[df['age'] < 15,'inc'] = 'Less than 15'


	for cat in eduC.keys():
		newdf.loc[df['age'] >= 25,'edu'] = newdf.loc[df['age'] >= 25,'edu'].replace(eduC[cat], cat)

	newdf.loc[df['age'] >= 15, 'inc'] = pd.cut(newdf.loc[df['age'] >= 15, 'inc'], 
		bins=[min(min(df['inc']),1), 9999,14999,24999,34999,49999,64999,74999,max(max(df['inc']),80000)],
		include_lowest = True, labels = incC.keys())

	categories['edu']['Less than 25'] = []
	categories['inc']['Less than 15'] = []
	
	return newdf, categories


def getPsJointDist(sample_df, categories):
	'''
	Get joint distribution from sample data
	Combinations in which no samples fall will be filled with 0

	'''

	productList = []
	subjects = sample_df.columns[3:]
	for sub in subjects:
		productList.append(categories[sub].keys())
	
	joint_dist = sample_df[subjects].groupby(list(subjects)).size()
	print joint_dist.shape
	Indexes = pd.MultiIndex.from_product(productList,names = subjects)
	
	# change index to all possible combinations of characteristics 
	# fill combinations where no sample fall with 0
	joint_dist = joint_dist.reindex(Indexes).fillna(0)
	print joint_dist.shape

	return joint_dist
	


def categorizeHhPUMS(dirname, hhfilename):
	rawdf = pd.read_csv(os.path.join(dirname, hhfilename))
	selectColumns = ['SERIALNO','PUMA','NP','VEH','HHT','HINCP','WIF']
	rawdf = rawdf[selectColumns]
	rawdf.columns.values[2:] = ['hh_size','vehicle','hh_type','hh_inc','workers']
	
	# IMPUTATION
	# one person household with income will be assigned with 1 worker
	rawdf.loc[(rawdf['hh_size'] == 1) &(rawdf['hh_inc'] > 0), 'workers'] = 1
	# drop records with na in any of variables we select
	rawdf.dropna(axis = 0, how='any',inplace =True)


	df = rawdf.copy()

	oldC,newC = {}, {}
	# household size 
	oldC['hh_size'] = range(1,21)
	newC['hh_size'] = np.repeat(['1-person household','2-person household',
	'3-person household','4-or-more-person household'],[1,1,1,20-3])
	# vehicle
	oldC['vehicle'] = range(0,7)
	newC['vehicle'] = np.repeat(['No vehicle available','1 vehicle available', 
		'2 vehicles available','3 vehicles available', '4 or more vehicles available'], [1,1,1,1,3])
	# hh_type
	oldC['hh_type'] = range(1,8)
	newC['hh_type'] = np.repeat(['Family households', 'Nonfamily households'],[3,4])
	# workers
	oldC['workers'] = range(0,4)
	newC['workers'] = ['No workers', '1 worker', '2 workers', '3 or more workers']

	subjects = df.columns[[2,3,4,6]]
	for sub in subjects:
		df[sub].replace(oldC[sub],newC[sub],inplace=True)

	# hh income
	inc_bins = [min(df['hh_inc']),14999,24999,34999, 44999,59999, 99999,149999,max(df['hh_inc'])]
	inc_labels = ['Less than $15,000', '$15,000 to $24,999', '$25,000 to $34,999', '$35,000 to $44,999',
	'$45,000 to $59,999', '$60,000 to $99,999', '$100,000 to $149,999', '$150,000 or more']
	df['hh_inc'] = pd.cut(df['hh_inc'],bins = inc_bins,include_lowest= True,labels = inc_labels)

	return df

	
def getHhJointDist(sample_df, one_marginal,two_marginal,mapCTtoPUMA,countyTable):

	'''
	this function takes all sample data of households as input
	then seperate those samples with respect to the county they belong to
	In each county, a joint distribution of all related variables are calculated from sample

	the output hh_joint_dist: is a dist, whose keys are names of the counties
	hh_joint_dist[county] is a MultiIndex Series, where each row is a combination of household,
	there are combination of households doesn't exist in sample data and will be recored as 0

	'''

	print sample_df.shape
	hh_joint_dist = {}
	for county in one_marginal.keys():
		countyId = countyTable.loc[countyTable['name'] == county,'id'].values[0]
		pumaInCounty = mapCTtoPUMA.loc[mapCTtoPUMA['COUNTYFP']==countyId,'PUMA5CE']

		pumaInCounty = [int(x) for x in pumaInCounty.tolist()]
		county_sample = sample_df[sample_df['PUMA'].isin(pumaInCounty)]
		
		subjects = one_marginal[county].keys()
		productList = []
		for sub in subjects:
			productList.append(one_marginal[county][sub].index)

		joint_dist = county_sample[subjects].groupby(list(subjects)).size()
		#print joint_dist

		Indexes = pd.MultiIndex.from_product(productList, names = subjects)
		hh_joint_dist[county] = joint_dist.reindex(Indexes).fillna(0)

	return hh_joint_dist

	

#hh_sample_categorized = categorizeHhPUMS('data','ss15htx_clean.csv')







