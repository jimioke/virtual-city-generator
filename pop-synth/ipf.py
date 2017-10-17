from ipfn import *
import numpy as np
import pandas as pd
from categorize import *
import sys
from datetime import datetime



def getIPFresult_for_county(marginal1d, marginal2d, joint_dist, 
	tolerance = 1e-3, max_iterations = 500, jd_zero_sub = 0.001):

	'''
	the "marginals" is marginal distributions of varaibles in the level of county
	joint_dist should be joint distribution generated from sample data in a county 

	marginals - MultiIndex pandas Series
	joint_dist - MultiIndex pandas Series developed from product

	'''
	# joint distribution needs zero cells to be augmented
	# zero cell problem
	df = joint_dist.rename('total').reset_index()
	df.replace(0, jd_zero_sub, inplace = True)

	aggregates = []
	dimensions = []
	#for key in marginals.index.levels[0]:
	#	aggregates.append(marginals[key])
	for key in marginal1d.keys():
		aggregates.append(marginal1d[key])
		dimensions.append([key])
	for key in marginal2d.keys():
		aggregates.append(marginal2d[key])
		dimensions.append([key[0], key[1]])

	IPF = ipfn(df, aggregates, dimensions,convergence_rate = tolerance, max_iteration = max_iterations)
	result = IPF.iteration()

	return result
	




def setup_IPF_for_Ps(df, marginalDF, countyTable, mapCTtoPUMA, categories):

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



def setup_IPF_for_Hh(one_marginal, two_marginal, hh_joint_dist, out_dir, write = True): 

	'''
	Select sample data and aggregate for each county
	Then perform IPF on selected data
	Return IPF result for each county

	'''

	ipf_results = {}
	for county in one_marginal.keys():
		#print one_marginal[county]
		time1 = datetime.now()
		ipf_result = getIPFresult_for_county(one_marginal[county],two_marginal[county], hh_joint_dist[county])
		print datetime.now()-time1
		ipf_results[county] = ipf_result

		#break

		#print ipf_result
		if write:
			jd = hh_joint_dist[county].rename('sample').reset_index()
			subjects = jd.columns.values[:-1]
			jd_and_ipf = pd.merge(jd,ipf_result, on=list(subjects))
			jd_and_ipf.to_csv(os.path.join(out_dir, county+'ipf_result.csv'))

	return ipf_results










