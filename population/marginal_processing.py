import pandas as pd
import os
import itertools
import numpy as np



def getHhMarginalFrom2D(dirname, filename, subjects, one_marginal, two_marginal):
	'''
	subjects - two dimension list, the first subject should be the first hierarchy in the table
	one_marginal - two level dict, the keys of first layer is county name, 
					the keys for the second level is the attribute name,
					values are 1D marginal distributions for those attributes in the county
	two_marginal - two level dict, the first level is the same as 'one_marginal'
					the second level uses 2D tuple as keys
					values are 2d marginal distribution for two attributes in the key

	'''

	table = pd.read_csv(os.path.join(dirname, filename),skiprows = [0])

	# Keep only columns with keywork "Estimate"
	columnsToDrop = [col for col in table.columns[3:] if col.split(';')[0] != 'Estimate']
	table.drop(columnsToDrop,1,inplace = True)
	
	nrow, ncol = table.shape

	for i in range(nrow):
		county = table['Geography'][i]
		if county not in one_marginal.keys():
			one_marginal[county] = {}
			two_marginal[county] = {}
		cat1, num1, cat2, num2, joint1, joint2, num = [],[],[],[],[],[],[]
		for j in range(3,ncol):
			colname = table.columns[j].split(';')[-1].strip()
			# first level of 1D marginal distribution 
			if colname.count(':')== 1 and colname.split(':')[-1] != '':
				catname = colname.split(':')[-1]
				cat1.append(catname[catname.find('-')+2:])
				num1.append(table.iloc[i,j])
			# second level of 1D marginal distribution 
			elif colname.count(':') == 2 and colname.split(':')[-1] == '':
				catname = colname.split(':')[-2]
				cat2.append(catname[catname.find('-')+2:])
				num2.append(table.iloc[i,j])
			elif colname.count(':') == 2 and colname.split(':')[-1] != '':
				c1, c2 = colname.split(':')[-2], colname.split(':')[-1]
				if c2[c2.find('-')+2:] == '3 workers':
					c2 = ' - 3 or more workers'
				joint1.append(c1[c1.find('-')+2:])
				joint2.append(c2[c2.find('-')+2:])
				num.append(table.iloc[i,j])

		
		# only add 1d marginal distribution if it hasn't been calculated before
		if (subjects[0] not in one_marginal[county].keys()):
			one_marginal[county][subjects[0]] = pd.Series(num1, index = cat1)
		if (subjects[1] not in one_marginal[county].keys()):
			one_marginal[county][subjects[1]] = pd.Series(num2, index = cat2)
		
		prodIndex = pd.MultiIndex.from_product([cat1, cat2], names = subjects)
		df = pd.Series(num, index = [joint2, joint1])
		# transfer sparse 2D index to dense 2D index
		two_marginal[county][subjects] = df.reindex(prodIndex).fillna(0)


	return one_marginal, two_marginal

def getHhMarginalFrom2D_B11016(dirname, filename, subjects, one_marginal, two_marginal):
	'''
	subjects - two dimension list, the first subject should be the first hierarchy in the table
	one_marginal - two level dict, the keys of first layer is county name, 
					the keys for the second level is the attribute name,
					values are 1D marginal distributions for those attributes in the county
	two_marginal - two level dict, the first level is the same as 'one_marginal'
					the second level uses 2D tuple as keys
					values are 2d marginal distribution for two attributes in the key

	'''

	table = pd.read_csv(os.path.join(dirname, filename),skiprows = [0])

	# Keep only columns with keywork "Estimate"
	columnsToDrop = [col for col in table.columns[3:] if col.split(';')[0] != 'Estimate']
	table.drop(columnsToDrop,1,inplace = True)
	
	nrow, ncol = table.shape

	for i in range(nrow):
		county = table['Geography'][i]
		if county not in one_marginal.keys():
			one_marginal[county] = {}
			two_marginal[county] = {}
		cat1, num1, joint1, joint2, num = [],[],[],[],[]
		for j in range(3,ncol):
			colname = table.columns[j].split(';')[-1].strip()
			# first level of 1D marginal distribution 
			if colname.count(':')== 1 and colname.split(':')[-1] == '' and colname.split(':')[0].strip() != 'Total':
				catname = colname.split(':')[0].strip()
				cat1.append(catname)
				num1.append(table.iloc[i,j])
			# second level of 1D marginal distribution 
			elif colname.count(':') == 1 and colname.split(':')[-1] != '':
				c1, c2 = colname.split(':')[-2].strip(), colname.split(':')[-1]
				# aggregate household size >=4 to one category
				if c2[c2.find('-')+2:] in ['4-person household','5-person household','6-person household','7-or-more person household']:
					c2 = ' - 4-or-more-person household'
				joint1.append(c1)
				joint2.append(c2[c2.find('-')+2:])
				num.append(table.iloc[i,j])

		
		if (subjects[1] not in one_marginal[county].keys()):
			one_marginal[county][subjects[1]] = pd.Series(num1, index = cat1)
		cat2 = one_marginal[county][subjects[0]].index
		prodIndex = pd.MultiIndex.from_product([cat2,cat1],names = subjects)
		df = pd.Series(num, index = [joint2, joint1])
		two_marginal[county][subjects] = df.groupby(level = [0,1]).sum().reindex(prodIndex).fillna(0)


	return one_marginal, two_marginal


def getHhMarginalFrom2D_B19001(dirname, filename, subject, one_marginal):


	table = pd.read_csv(os.path.join(dirname, filename),skiprows = [0])

	# Keep only columns with keywork "Estimate"
	columnsToDrop = [col for col in table.columns[3:] if col.split(';')[0] != 'Estimate']
	table.drop(columnsToDrop,1,inplace = True)
	
	nrow, ncol = table.shape

	catnew = np.repeat(['Less than $15,000', '$15,000 to $24,999', '$25,000 to $34,999', '$35,000 to $44,999',
	'$45,000 to $59,999', '$60,000 to $99,999', '$100,000 to $149,999', '$150,000 or more'],[2]*8)

	for i in range(nrow):
		county = table['Geography'][i]
		if county not in one_marginal.keys():
			one_marginal = {}
		cat, num = [],[]
		for j in range(3,ncol):
			colname = table.columns[j].split(';')[-1]
			if colname.find('-') > -1:
				cat.append(colname.split('-')[-1].strip())
				num.append(table.iloc[i,j])

		df = pd.Series(num, index = catnew)

		one_marginal[county][subject] = df.groupby(level = 0).sum()

	return one_marginal
			

def print_marginal_categories(marginals):

	# print all categories of each variable in format of:
	# varable: category1; category2
	county = marginals.keys()[0]
	dic = marginals[county]
	for sub in dic.keys():
		cats = dic[sub].keys()
		print sub+': '+'; '.join(cats)



def main_marginal_process(dirname, marginal_files):


	marginal_filenames = []
	one_marginal, two_marginal = {}, {}
	# get marginal distribution from B08202
	subjects = ('workers','hh_size')
	one_marginal, two_marginal = getHhMarginalFrom2D(dirname,marginal_files[0],subjects, one_marginal, two_marginal)

	# get marginal distribution from B08203
	subjects = ('vehicle','workers')
	one_marginal, two_marginal = getHhMarginalFrom2D(dirname,marginal_files[1],subjects, one_marginal, two_marginal)

	# get marginal distribution from B11016
	subjects = ('hh_size','hh_type')
	one_marginal, two_marginal = getHhMarginalFrom2D_B11016(dirname,marginal_files[2], subjects, one_marginal, two_marginal)

	# get marginal distribution from B19001
	subject = 'hh_inc'
	one_marginal = getHhMarginalFrom2D_B19001(dirname,marginal_files[3], subject, one_marginal)


	# check output of one_marginal
	
	'''
	for county in one_marginal.keys():
		if county[0] == 'A':
			print county
			for sub in one_marginal[county]:
				print sub
				print one_marginal[county][sub]
				print sum(one_marginal[county][sub])




	# check output of two_marginal 

	for county in two_marginal.keys():
		if county[0] == 'A':
			print county 
			for sub in two_marginal[county]:
				print sub
				print two_marginal[county][sub]
				print sum(two_marginal[county][sub])
	'''

	return one_marginal, two_marginal

	
def write_aggregate_data(one_marginal, two_marginal, out_dir):
	'''
	write output file for aggregate data

	'''

	aggregates_1d = []
	aggregates_2d = []
	for county in one_marginal.keys():
		distributions = []
		for dist in one_marginal[county].keys():
			distributions.append(one_marginal[county][dist])
		df = pd.concat(distributions, keys = one_marginal[county].keys()).rename(county)
		aggregates_1d.append(df)
		distributions = []
		for dist in two_marginal[county].keys():
			distributions.append(two_marginal[county][dist])
		df = pd.concat(distributions, keys = two_marginal[county].keys()).rename(county)
		aggregates_2d.append(df)
	
	marginals1d = pd.concat(aggregates_1d, axis = 1)
	marginals2d = pd.concat(aggregates_2d, axis = 1)
	marginals1d.to_csv(os.path.join(out_dir,'hh_marginals_1d.csv'))
	marginals2d.to_csv(os.path.join(out_dir,'hh_marginals_2d.csv'))





'''
dirname = 'data'
marginal_files = ['ACS_15_5YR_B08202.csv','ACS_15_5YR_B08203.csv','ACS_15_5YR_B11016.csv','ACS_15_5YR_B19001.csv'] 
one_marginal, two_margina = main_marginal_process(dirname, marginal_files)
print_marginal_categories(one_marginal)
'''



