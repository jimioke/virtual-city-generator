
# coding: utf-8

# In[15]:

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





def getGraph(location, type='drive'):
	# gdf = ox.gdf_from_place(location)
	# areaSqM = ox.project_gdf(gdf).unary_union.area
	try:
		G = ox.graph_from_place(location, network_type='drive')
		ox.plot_graph(ox.project_graph(G))
	except ValueError:
		G = ox.graph_from_place(location, network_type='drive',which_result=2)
	return G #, areaSqM

g = getGraph('Mountainside,NJ,USA')

def getNormalizedLatLongs(X,Y)
    xbar = np.average(X)
    ybar = np.average(Y)
    normalizedx = X-xbar
    normalizedy = Y-ybar

    return normalizedx, normalizedy



# In[2]:

edges = g.edges(data=True)

#print(edges)

edgeinfo = pd.DataFrame.from_dict(g.edges(data=True))

edgeinfo = pd.concat([edgeinfo,pd.DataFrame(edgeinfo[2].tolist())],axis=1)

edgeinfo = edgeinfo.drop(2,axis=1)

print(edgeinfo)



# In[3]:

connectionmatrix = nx.to_pandas_dataframe(g)
print(connectionmatrix)


# In[4]:

distancematrix = connectionmatrix
for x in range(0,edges.__len__()):
    distancematrix[edges[x][0]][edges[x][1]] = edges[x][2]['length']
    
    



# In[5]:

print(distancematrix)
distancematrix.to_csv('distanceMatrix.csv')


# In[6]:

shortestpaths = nx.all_pairs_shortest_path_length(g)




# In[7]:

shortestpathsmatrix = pd.DataFrame(shortestpaths)
print (shortestpathsmatrix)


# In[8]:

print(g.nodes(data=True))


# In[9]:

gn = pd.DataFrame.from_dict(g.nodes(data=True))

gn = pd.concat([gn,pd.DataFrame(gn[1].tolist())],axis=1)

gn = gn.drop(1,axis=1)

print(gn)

print(gn['x'])







# In[10]:

nx.write_gpickle(g, "test.gpickle")


# In[28]:

h = nx.read_gpickle("Buenos_Aires_Argentina.gpickle")


# In[12]:

print(h.edges(data=True))


# In[44]:

def kde1(x, y, ax):
    from scipy.stats import gaussian_kde
    
    # Calculate the point density
    xy = np.hstack([x,y])
    kernel = gaussian_kde(xy, bw_method='silverman')

    xmin = x.min()
    xmax = x.max()
    ymin = y.min()
    ymax = y.max()
    
    X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = np.vstack([X.ravel(), Y.ravel()])

    Z = np.reshape(kernel(positions).T, X.shape)

    ax.imshow(np.rot90(Z), cmap=plt.cm.viridis,
              extent=[xmin, xmax, ymin, ymax])
    
    ax.scatter(x, y, c='k', s=5, edgecolor='')
    
    return kernel
    

    
fig, axarr = plt.subplots(1, 2)
ax = axarr[0]
k1 = kde1(gn['x'],gn['y'],ax)
# https://gist.github.com/daleroberts/7a13afed55f3e2388865b0ec94cd80d2

plt.show()






# In[29]:

redraw = k1.resample(333)


# In[25]:

plt.scatter(redraw[0],redraw[1])
plt.show()


# In[33]:

xbar = np.average(gn['x'])
ybar = np.average(gn['y'])

normalizedx = gn['x']-xbar
normalizedy = gn['y']-ybar

x,y = getNormalizedLatLongs(gn['x'],gn['y'])



# In[45]:

fig, axarr = plt.subplots(1,2)
ax = axarr[0]

k1 = kde1(normalizedx[:],normalizedy[:],ax)
# https://gist.github.com/daleroberts/7a13afed55f3e2388865b0ec94cd80d2

plt.show()


# In[ ]:



