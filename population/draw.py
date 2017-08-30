import pandas as pd
import numpy as np
from collections import OrderedDict
import itertools
import os


def simple_draw(tot,weights):


	'''
	Input:
	weights - is MultiIndex Series with index indicates the categories of variables,
			  the data gives the weight of this combination of categories

	'''

	p = weights/weights.sum()
	index = weights.index.values.tolist()
	print index
	return np.random.choice(len(index), size = tot, p = p, replace = True)



def draw_synth_hh(ipf_results, hh_sample, ps_sample,mapCTtoPUMA, countyTable, out_dir):
	'''
	Input:
	ipf_results: dictionary with keys represent a county
	ipf_results[counyt]: dataframe, first columns record categories for variables 
						 while the last column 'total' is the weight for this combination
	hh_sample: dataframe, first columns are 'SERIALNO','PUMA'
	ps_sample: dataframe, first columns are 'SERIALNO','SPORDER','PUMA'
	
	do MC sampling based on weights in ipf result

	'''

	synth_hh = []
	synth_ps = []
	i = 0
	for county in ipf_results.keys():
		i += 1
		# modify index for weights
		ipf_result = ipf_results[county]
		index_title = list(ipf_result.columns.values[:-1])
		index_title.sort()
		tot = sum(ipf_result['total'])

		# select sample in this county
		countyId = countyTable.loc[countyTable['name'] == county,'id'].values[0]
		pumaInCounty = mapCTtoPUMA.loc[mapCTtoPUMA['COUNTYFP']==countyId,'PUMA5CE']
		pumaInCounty = [int(x) for x in pumaInCounty.tolist()]
		# household and person sample in the county
		hhspc = hh_sample[hh_sample['PUMA'].isin(pumaInCounty)]
		psspc = ps_sample[ps_sample['PUMA'].isin(pumaInCounty)]

		# merge weights of each type of household with household sample data
		merge_df = pd.merge(hhspc,ipf_result, on=index_title)
		#merge_df.to_csv(os.path.join(out_dir,'merge_test.csv')

		columnsToKeep = merge_df.columns[:-1]
		synth_hh_c = merge_df[columnsToKeep].sample(int(tot),replace = True,weights = merge_df['total'])
		synth_hh_c.reset_index(drop=True,inplace=True)
		synth_hh_c.index += i*10000000
		synth_hh_c['county'] = countyId
		synth_hh_c.index.name = 'hh_newid'
		# write synthetic household in this county to a csv file
		synth_hh_c.to_csv(os.path.join(out_dir, county+'synth_hh.csv'))
		synth_hh.append(synth_hh_c)

		subdf = pd.DataFrame({
			'SERIALNO': synth_hh_c['SERIALNO'],
			'hh_newid': synth_hh_c.index.values
		})
		
		synth_ps_c = pd.merge(psspc, subdf, left_on = 'SERIALNO', right_on='SERIALNO')
		synth_ps_c['county'] = countyId
		synth_ps_c.to_csv(os.path.join(out_dir, county+'synth_ps.csv'))
		synth_ps.append(synth_ps_c)		



	synth_hh = pd.concat(synth_hh)
	synth_ps = pd.concat(synth_ps)
	synth_hh.to_csv(os.path.join(out_dir, 'synth_hh.csv'))
	synth_ps.to_csv(os.path.join(out_dir, 'synth_ps.csv'))

	return synth_hh, synth_ps


def test_merge():
	a = pd.DataFrame({
		'Serialno':[11,11,22,22,22,33,44,44],
		'ps_id': [1,2,1,2,3,1,1,2] 
		})

	b = pd.DataFrame({
		'Serialno':[11,11,11,33,33,33,33,33],
		'hh_id' :[1,2,3,4,5,6,7,8]
		})


	hh_df = pd.DataFrame(
	    {'a': range(5),
	     'b': range(5, 10),
	     'serialno': [11, 22, 33, 44, 55]},
	    index=pd.Index(['a', 'b', 'c', 'd', 'e'], name='hh_id'))

	pp_df = pd.DataFrame(
	    {'x': range(100, 110),
	     'y': range(110, 120),
	     'serialno': [22, 33, 11, 55, 22, 33, 44, 55, 11, 33]},
	    index=pd.Index(['q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']))

	indexes = ['c', 'a', 'd', 'e', 'a', 'c', 'e', 'e', 'a', 'c', 'e']

	synth_hh = hh_df.loc[indexes].reset_index(drop=True)
	synth_hh.index += 1000
	mrg_tbl = pd.DataFrame(
	        {'serialno': synth_hh.serialno.values,
	         'hh_id': synth_hh.index.values})

	synth_people = pd.merge(
	        pp_df, mrg_tbl, left_on='serialno', right_on='serialno')

