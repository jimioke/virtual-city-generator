import osmnx as ox
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from stateDict import us_state_abbrev
from operator import eq, contains
import sys
import logging
import signal
import utils
from utils import *
from sklearn.neighbors import KernelDensity
from scipy.stats.distributions import norm
import plotly.plotly as py
import plotly.graph_objs as go


citylist = ['Mountainside,NJ,USA','Springfield,NJ,USA','Morristown,NJ,USA','Westfield,NJ,USA','Plainfield,NJ,USA', 'Summit,NJ,USA', 'South Plainfield,NJ,USA', 'Scotch Plains,NJ,USA', 'Garwood,NJ,USA', 'Kenilworth,NJ,USA']

#save graphs of city list
#for cities in citylist:
#    saveGraph(getGraph(cities),cities)

#load the saved city graphs
graphs_for_analysis = []
for cities in citylist:
    graphs_for_analysis.append(loadGraph(cities))


#get the node data into a data frame
node_data = []
i = len(graphs_for_analysis)
for graphs in range(0,i):
    node_data.append(getNodeDataFrame(graphs_for_analysis[graphs]))


j = len(node_data)
count = 0 
norm_matrices = []
for node_dfs in range(0,j):
    norm_matrices.append(getNormalizedLatLongsMatrix(node_data[node_dfs]))

print(norm_matrices[0].shape)
print(norm_matrices[0])