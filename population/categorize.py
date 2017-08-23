
import pandas as pd 
import numpy as np 
import os
import math

def categorizePersonPUMS(dirname, psfilename):

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
	for sub in ['sex','age','mar']:
		for cat in categories[sub].keys():
			newdf[sub] = newdf[sub].replace(categories[sub][cat],cat)

	# categorize education attainment and income

	newdf.loc[df['age'] < 15,'edu'] = 'Less than 15'
	newdf.loc[df['age'] < 15,'inc'] = 'Less than 15'


	for cat in eduC.keys():
		newdf.loc[df['age'] >= 15,'edu'] = newdf.loc[df['age'] >= 15,'edu'].replace(eduC[cat], cat)

	newdf.loc[df['age'] >= 15, 'inc'] = pd.cut(newdf.loc[df['age'] >= 15, 'inc'], 
		bins=[min(min(df['inc']),1), 9999,14999,24999,34999,49999,64999,74999,max(max(df['inc']),80000)],
		include_lowest = True, labels = incC.keys())

	return newdf






dirname = 'data'
psfilename = 'ss15ptx_clean.csv'
person = categorizePersonPUMS(dirname, psfilename)

