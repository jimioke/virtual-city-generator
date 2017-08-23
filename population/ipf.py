from ipfn import *
import numpy as np
import pandas as pd
from categorize import *



def getIPFresult_for_county(marginals, joint_dist, 
	tolerance = 1e-3, max_iterations = 1000):

	'''
	the "marginals" is marginal distributions of varaibles in the level of county
	joint_dist should be joint distribution generated from sample data in a county 

	marginals - MultiIndex pandas Series
	joint_dist - MultiIndex pandas Series developed from product

	'''

	df = joint_dist.rename('total').reset_index()

	aggreagtes = []
	for key in marginals.index.levels[0]:
		aggregates.append(marginals[key])

	dimensions = [[key] for key in marginals.index.levels[0]]

	IPF = ipfn(df, aggregates, dimensions)
	result = IPF.iteration()

	return result




def setup_IPF_for_county(df, marginalDF, countyTable, mapCTtoPUMA, categories):

	'''
	Do IPF one by one in the level of county

	'''

	counties = marginalDF.columns

	results = []
	for county in counties:
		countyID = countyTable[countyTable['name'] == county]['id']
		pumaID_in_county = mapCTtoPUMA[mapCTtoPUMA['COUNTYFP'] == countyID]['PUMA5CE']
		# select sample data and marginals for this county
		sample_of_county = df[df['PUMA'].isin(pumaID_in_county)]
		marginal_of_county = marginalDF[county]
		# get joint distribution of sample data in the county

		joint_dist_of_county = getPsJointDist(sample_of_county, categories)
		county_result = getIPFresult_for_county(marginal_of_county, joint_dist_of_county)
		result.append(county_result)

	result = pd.concat(results, axis = 1)
	return result


