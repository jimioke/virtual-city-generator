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

##get the list of cities to import
##note: change to load list from CSV file
citylist = ['Mountainside,NJ,USA','Springfield,NJ,USA','Morristown,NJ,USA','Westfield,NJ,USA','Plainfield,NJ,USA', 'Summit,NJ,USA', 'South Plainfield,NJ,USA', 'Scotch Plains,NJ,USA', 'Garwood,NJ,USA', 'Kenilworth,NJ,USA']

#load the saved city graphs
graphs_for_analysis = []
for cities in citylist:
    graphs_for_analysis.append(loadGraph(cities))

#get the node data into a data frame
node_data = []
i = len(graphs_for_analysis)
for graphs in range(0,i):
    node_data.append(getNodeDataFrame(graphs_for_analysis[graphs]))
    #ox.plot_graph(ox.project_graph(graphs_for_analysis[graphs]))

#get total node count
j = len(node_data)
count = 0 
for node_dfs in range(0,j):
    count+=len(node_data[node_dfs].index)

#build empty lat/long arrays
lat = np.zeros(shape=[count,1])
longitude = np.zeros(shape=[count,1])

#normalize latitude and longitude arrays
index = 0
counter = 0
for node_dfs in range(0,j):
    index+=counter
    counter = len(node_data[node_dfs].index)
    for k in range(index,index+counter):
        lat_temp,longitude_temp = getNormalizedLatLongs(node_data[node_dfs])
        lat[k] = lat_temp[k-index]
        longitude[k] = longitude_temp[k-index]

        
kde = getKernelDensity(lat,longitude)

redrawsk = kde.sample(n_samples=500)
print(redrawsk.shape)


plt.scatter(redrawsk[:,0]/100,redrawsk[:,1]/100)
plt.title('500 Samples Pulled from 10 NJ Towns Distribution')
plt.xlabel('normalized latitude')
plt.ylabel('normalized longitude')
plt.show()

plt.scatter(lat[:],longitude[:])
plt.title('All Lat/Long Pairs from 10 NJ Towns (5,000+ points)')
plt.xlabel('normalized latitude')
plt.ylabel('normalized longitude')
plt.show()






# In[3]:

#print(redrawsk)
points = np.matrix(redrawsk)
print(points)


# In[4]:

GT = nx.Graph()
#GT.add_nodes_from(points)

keys = np.arange(500).reshape(500,1)

comb = np.concatenate((keys,points),axis=1)
print(comb[0])

r, c = np.shape(comb)
for i in range (0, r):
    GT.add_node(comb[i,0], pos=(comb[i,1],comb[i,2]))


#dic = [{'key': comb[0,0], 'x': comb[0,1], 'y': comb[0,2]} for comb in comb]

#print(dic[0]['key'])


print(GT.nodes(data=True))


# In[6]:

pos=nx.get_node_attributes(GT,'pos')
nx.draw(GT,pos,node_size=10)
plt.show()



# In[10]:

#http://stackoverflow.com/questions/12923586/nearest-neighbor-search-python

from scipy.spatial import cKDTree

#create numpy array with four nearest neighbors
nn = np.zeros(shape=[r,10])
tree = cKDTree(points, leafsize=100)
i=0
for item in points:
    TheResult = tree.query(item, k=5)
    nn[i] = np.concatenate((TheResult[0],TheResult[1]),axis=1)
    i+=1
    
#    nn[item,0] = item
#    nn[item,1] = TheResult[0]
    

print(nn[499])

    


# In[11]:

iters=0
for j in range (0, r):
    for l in (6,7,8,9):
#        print('u',nn[j,5])
#        print('v',nn[j,l])
#        print('dist',nn[j,l-5])
        if( GT.has_edge(nn[j,5],nn[j,l])==False):
            GT.add_edge(nn[j,5],nn[j,l], dist=nn[j,l-5])
        iters+=1
        
print(iters)
        
print(GT.edges(data=True))


# In[12]:

nx.draw(GT,pos,hold=None,node_size=10)
plt.show()


# In[13]:

adj = getAdjacencyDataFrame(GT)
print(adj)



# In[14]:

shortpath = getShortestPathDataFrame(GT)
print(shortpath)


# In[21]:

print('shortest path shape:',shortpath.shape)
print('adjacency matrix shape:',adj.shape)


# In[ ]:

## repeat process for each input graph


