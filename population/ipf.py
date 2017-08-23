from ipfn import *
import numpy as np
import pandas as pd



def getIPFresult(marginals, joint_dist, tolerance = 1e-3, max_iterations = 1000):

	'''
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








