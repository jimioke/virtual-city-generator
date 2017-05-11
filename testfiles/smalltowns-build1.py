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
    #ox.plot_graph(ox.project_graph(graphs_for_analysis[graphs]))

j = len(node_data)
count = 0 
for node_dfs in range(0,j):
    count+=len(node_data[node_dfs].index)

lat = np.zeros(shape=[count,1])
longitude = np.zeros(shape=[count,1])

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

G = nx.to_networkx_graph()
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


# #http://stackoverflow.com/questions/41577705/how-does-2d-kernel-density-estimation-in-python-sklearn-work
#freq = np.concatenate([ norm(8,2.).rvs(100), norm(18,1.).rvs(100) ])
# xy_sample = np.hstack([lat,longitude])
# Z = np.zeros(shape=[count,1])
# Z[:,0] = np.exp(kde.score_samples(xy_sample))

# X, Y = np.meshgrid(lat, longitude)
# levels = np.linspace(0, Z.max(), 25)
# Z = Z.reshape(X.shape)
# plt.contourf(X, Y, Z, levels=levels, cmap=plt.cm.Reds)

# plt.show()

# print(lat.size)
# print(longitude.size)
# print(z.size)
# z2 = np.hstack([lat,longitude,z])
# print(z2)


# # https://gist.github.com/daleroberts/7a13afed55f3e2388865b0ec94cd80d2

# print(lat.shape)
# print(longitude.shape)
# print(z.shape)

# xx, yy = np.meshgrid(lat,longitude)
# print(np.exp(kde.score_samples(xx,yy)))
# print(xx.shape)
# print(yy.shape)
# print(xx)
# print(yy)
# plt.figure()
# cp = plt.contourf(xx,yy,zz)
# plt.colorbar(cp)
# plt.show()
# # data = [
# #     go.Contour(
# #         z=zz,
# #         x=lat,
# #         y=longitude
# #     )]

# # py.iplot(data)


# # xbins=100j
# # ybins=100j

# # xx, yy = np.mgrid[lat.min():lat.max():xbins, 
# #                     longitude.min():longitude.max():ybins]
# # z_min, z_max = -np.abs(zz).max(), np.abs(zz).max()


# # score_samples() returns the log-likelihood of the samples

# #plt.pcolormesh(xx, yy, zz)
# plt.scatter(lat, longitude, s=2, facecolor='white')

# plt.pcolormesh(xx, yy, zz, cmap='RdBu', vmin=z_min, vmax=z_max)
# plt.title('pcolormesh')
# # set the limits of the plot to the limits of the data
# plt.axis([x.min(), x.max(), y.min(), y.max()])
# plt.colorbar()
# plt.plot()



# # from sklearn.grid_search import GridSearchCV

# # #http://mark-kay.net/2013/12/24/kernel-density-estimation/

# # grid = GridSearchCV(KernelDensity(),
# #                     {'bandwidth': np.linspace(0.1, 1.0, 30)},
# #                     cv=20) # 20-fold cross-validation
# # grid.fit(freq[:, None])
# # print (grid.best_params_)


# redrawsk = kde.sample(n_samples=250)

# plt.scatter(redrawsk[:,0],redrawsk[:,1])
# plt.show()


# plt.scatter(lat[:],longitude[:])
# plt.show()

# xmin = x.min()
# xmax = x.max()
# ymin = y.min()
# ymax = y.max()

# X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
# positions = np.vstack([X.ravel(), Y.ravel()])

# Z = np.reshape(np.exp(kde.score_samples(positions.T)), X.shape)

# ax.imshow(np.rot90(Z), cmap=plt.cm.viridis,
#             extent=[xmin, xmax, ymin, ymax])

# ax.scatter(x, y, c='k', s=5, edgecolor='')
