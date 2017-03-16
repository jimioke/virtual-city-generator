import osmnx as ox
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.cm as cm
from stateDict import us_state_abbrev
from operator import eq, contains
import sys
import logging
import signal

ox.config(log_file=False, log_console=False, use_cache=True)
logging.basicConfig(level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s',
	filename="roadNets.log", #"{:s}_{:s}.log".format(todaysDate, timeNow),
	filemode='w')

class TimeoutException(Exception):
	pass

def timeout_handler(signum, frame):  
	raise TimeoutException

#signal.signal(signal.SIGALRM, timeout_handler)

# df = pd.read_csv('../../citiesabridged.csv')
# df = df[['City','Country']]

# dd = pd.DataFrame(columns=['City','Country', #'AreaSqM',
# 				#'AveBC','AveCC','Radius', 
# 				#'InterDens', 'StreetDens', 
# 				'CircuityAvg','EdgeLenAvg',
# 				'StreetLenTot'])
# #dd.City = df['City']
# #dd.Country = df['Country']
# dd.to_csv('roadStats.csv',index=False)

def keyOfValue(dct, value, ops = (eq, contains)):
	for k in dct:
		if ops[isinstance(dct[k], list)](dct[k], value):
			return k

def getPlaceName(index):
	city = df.loc[index,'City']
	country = df.loc[index,'Country']
	if '(' in city:
		cityName = city.split('(',1)[0]
		stateAbb = city.split('(',1)[1].split(')')[0]
		stateFull = keyOfValue(us_state_abbrev, stateAbb)
		location = cityName+', '+stateFull+', '+country
	else:
		location = city+', '+country
	return location


def getGraph(location, type='drive'):
	# gdf = ox.gdf_from_place(location)
	# areaSqM = ox.project_gdf(gdf).unary_union.area
	try:
		G = ox.graph_from_place(location, network_type='drive')
		ox.plot_graph(ox.project_graph(G))
	except ValueError:
		G = ox.graph_from_place(location, network_type='drive',which_result=2)
	return G #, areaSqM

def getStats(G): #, areaSqM):
	stats = ox.basic_stats(G) #, area=areaSqM)
	# extendedStats = ox.extended_stats(G, ecc=False, bc=False, cc=False)
	#for key, value in extendedStats.items():
	#	stats[key] = value
	# for k, count in stats['streets_per_node_counts'].items():
	#     stats['int_{}_count'.format(k)] = count
	# for k, proportion in stats['streets_per_node_proportion'].items():
	#     stats['int_{}_prop'.format(k)] = proportion
	# del stats['streets_per_node_counts']
	# del stats['streets_per_node_proportion']
	# stats['area_sq_m'] = areaSqM
	stats = pd.DataFrame(pd.Series(stats)).T
	return stats

def writeToDataFrame(stats, index):
	dd.loc[index, 'City'] = df.loc[index, 'City']
	dd.loc[index, 'Country'] = df.loc[index, 'Country']
	#dd.loc[index, 'AreaSqM'] = stats['area_sq_m']
	#dd.loc[index, 'AveBC'] = stats['betweenness_centrality_avg']
	#dd.loc[index, 'AveCC'] = stats['closeness_centrality_avg']
	#dd.loc[index, 'Radius'] = stats['radius']
	#dd.loc[index, 'InterDens'] = stats['intersection_density_km']
	#dd.loc[index, 'StreetDens'] = stats['street_density_km']
	dd.loc[index, 'CircuityAvg'] = stats['circuity_avg'][0]
	dd.loc[index, 'EdgeLenAvg'] = stats['edge_length_avg'][0]
	dd.loc[index, 'StreetLenTot'] = stats['street_length_total'][0]
	dd.to_csv('roadStats.csv',index=False)
	logging.info('Written road stats for {:s} to dataframe.'.format(dd.loc[index, 'City']))
	return

def main():

	g = getGraph('Mountainside, NJ, USA', type='drive')
	return g

	# G = ox.graph_from_place('Manhattan, New York, USA', network_type='drive')
	# ox.plot_graph(ox.project_graph(G))


	'''	
	indexGen = (i for i in df.index[84:]) #broke at Ecuador, Guayaquil index 83, now start from Quito
	while True:
		ind = indexGen.next()
		signal.alarm(300) # start timer
		try:
			location = getPlaceName(ind)
			# G, areaSqM = getGraph(location)
			G = getGraph(location)
			stats = getStats(G) #, areaSqM)
			writeToDataFrame(stats, ind)
		except ValueError:
			e = sys.exc_info()
			logging.error(e)
			continue
		except NameError:
			e = sys.exc_info()
			logging.error(e)
			continue
		except TimeoutException:
			logging.info('Timeout. Moving on to next city...')
			continue
		except KeyError:
			e = sys.exc_info()
			logging.error(e)
			continue
		except:
			e = sys.exc_info()
			logging.error(e)
			continue
		else:
			signal.alarm(0) # reset timer'''

if __name__ == "__main__":
	main()
