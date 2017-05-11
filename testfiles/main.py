import osmnx as ox
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from stateDict import us_state_abbrev
from operator import eq, contains
from scipy.stats import gaussian_kde
import sys
import logging
import signal
from sklearn.neighbors import KernelDensity
from math import radians, cos, sin, asin, sqrt
import utils
from utils import *
from scipy.spatial import cKDTree
from sklearn import linear_model
from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn import metrics
from sklearn.cross_validation import cross_val_score
from sklearn import svm

citylist = ['Mountainside,NJ,USA','Springfield,NJ,USA','Morristown,NJ,USA','Westfield,NJ,USA','Plainfield,NJ,USA', 'Summit,NJ,USA', 'South Plainfield,NJ,USA', 'Scotch Plains,NJ,USA', 'Garwood,NJ,USA', 'Kenilworth,NJ,USA']
#citylist = ['Mountainside,NJ,USA']
#load the saved city graphs
graphs = []
for cities in citylist:
    graphs.append(loadGraph(cities))

normfullconnectgraphs = []
for g in range(0,len(graphs)):
    normfullconnectgraphs.append(transformGraphToNormalizedFullyConnected(graphs[g],10))

print(getActualDistanceDataFrame(normfullconnectgraphs[0]))
dfstart = getNodeDataFrame(normfullconnectgraphs[0])
lat = dfstart['x'].values[:,np.newaxis]
longitude = dfstart['y'].values[:,np.newaxis]
for g in range(1,len(graphs)):
    df = getNodeDataFrame(normfullconnectgraphs[g])
    lat = np.concatenate((lat, df['x'].values[:,np.newaxis]))
    longitude = np.concatenate((longitude, df['y'].values[:,np.newaxis]))

# pos=nx.get_node_attributes(normfullconnectgraphs[1],'pos')
# nx.draw(normfullconnectgraphs[1],pos,hold=None,node_size=10)
# plt.show()

#df = getShortestPathDataFrame(normfullconnectgraphs[1])
#df.to_csv('springfieldshort.csv')

#edgeinfo = pd.DataFrame.from_dict(normfullconnectgraphs[1].edges(data=True))
#edgeinfo.to_csv('springfieldedge.csv')

adj, short, total_length = graphMatricesToAdjandShortestPath(graphs,normfullconnectgraphs)

#create one long vector for X and Y
X = short[0]
Y = adj[0]
for g in range (1,len(graphs)):
    X = np.concatenate((X,short[g]))
    Y = np.concatenate((Y,adj[g]))

#remove parts of cities that aren't connected to the rest of the city
isnan = np.where(np.isnan(X) == True)
X = np.delete(X, isnan[0])[:,np.newaxis]
Y = np.delete(Y, isnan[0])[:,np.newaxis]
print(X.shape)

# greater = np.where(X >= 4)
# X = np.delete(X, greater[0])[:,np.newaxis]
# Y = np.delete(Y, greater[0])[:,np.newaxis]
# print(np.sum(Y))
# print(X.shape)
#clf = linear_model.SGDClassifier()
#clf.fit(X, Y)
#clf = linear_model.LogisticRegression(C=1e5,max_iter=1000)
#clf.fit(X, Y)
# print('score',clf.score(X,Y))

nog,fcg = CreateFullyConnectedGraph(lat,longitude,500,10)

fcgsp = getShortestPathX(fcg)

# greater = np.where(fcgsp[:,2] >= 4)
# fcgsp = np.delete(fcgsp, greater[0], axis=0)

# print(fcgsp.shape)
# print(fcgsp)
#predictions = clf.predict(fcgsp[:,2][:,np.newaxis])
#print(np.max(predictions))
# print(predictions)
# print(np.sum(predictions))

#final = np.concatenate((fcgsp,predictions[:,np.newaxis]),axis=1)
#print(final)
#final.view('f8,f8,f8,f8').sort(order=['f3'], axis=0)
# print(final.shape)

lam = .01
pij = 1/(1+np.exp(lam*fcgsp[:,2]))

final = np.concatenate((fcgsp,pij[:,np.newaxis]),axis=1)
print(final.shape)
print(final)
final.view('f8,f8,f8,f8').sort(order=['f3'], axis=0)
# print(final)

iter=0
r,c = final.shape
for j in range (0,r):
    if( nog.has_edge(final[j,0],final[j,1])==False and iter<=500):
        nog.add_edge(final[j,0],final[j,1], origshortpath=final[j,2])
        iter+=1
print(iter)
#            print(iter)


pos=nx.get_node_attributes(nog,'pos')
nx.draw(nog,pos,hold=None,node_size=10)
plt.show()

pos=nx.get_node_attributes(fcg,'pos')
nx.draw(fcg,pos,hold=None,node_size=10)
plt.show()

#scores = cross_val_score(LogisticRegression(), X, Y.ravel(), scoring='accuracy', cv=10)
#print(scores)
#print(scores.mean())
# and plot the result
#plt.figure(1, figsize=(4, 3))
#plt.clf()
#plt.scatter(X.ravel(), Y, color='black', zorder=20)
#X_test = np.linspace(-5, 10, 300)
    

'''
adj = getAdjacencyDataFrame(graphs[0].to_undirected())
#adj.to_csv('adj.csv')
#adj = getAdjacencyDataFrame(graphs[0])
shortpath = getShortestPathDataFrame(normfullconnectgraphs[0])
print(np.sum(adj.values))
r,c = adj.shape
ind = np.triu_indices(r,k=1)
adj = adj.values[ind].flatten()[:,np.newaxis]
loop = np.where(adj > 1)
for l in loop:
    adj[l] = 1

shortpath = shortpath.values[ind].flatten()[:,np.newaxis]
regression = np.concatenate((adj,shortpath),axis=1)

print('adj',adj.shape)
print('shortest path', shortpath.shape)
print('regression', regression)
print('adj sum',np.sum(adj))
#np.savetxt('test.out', regression, delimiter=',') 
#NYC = getGraph('New York, NY, USA')

edgeinfo = pd.DataFrame.from_dict(graphs[0].edges(data=True))

h = .02  # step size in the mesh
X = shortpath
Y = adj
clf = linear_model.LogisticRegression(C=1e5)
clf.fit(X, Y)
print('score',clf.score(X,Y))
scores = cross_val_score(LogisticRegression(), X, Y.ravel(), scoring='accuracy', cv=10)
print(scores)
print(scores.mean())
# and plot the result
plt.figure(1, figsize=(4, 3))
plt.clf()
plt.scatter(X.ravel(), Y, color='black', zorder=20)
X_test = np.linspace(-5, 10, 300)


def model(x):
    return 1 / (1 + np.exp(-x))
loss = model(X_test * clf.coef_ + clf.intercept_).ravel()
plt.plot(X_test, loss, color='red', linewidth=3)
plt.show()

ols = linear_model.LinearRegression()
ols.fit(X, Y)
plt.plot(X_test, ols.coef_ * X_test + ols.intercept_, linewidth=1)
plt.axhline(.5, color='.5')

plt.ylabel('y')
plt.xlabel('X')
plt.xticks(range(-5, 10))
plt.yticks([0, 0.5, 1])
plt.ylim(-.25, 1.25)
plt.xlim(-4, 10)
plt.legend(('Logistic Regression Model', 'Linear Regression Model'),
           loc="lower right", fontsize='small')
plt.show()
#print(edgeinfo)



#G = transformGraphToNormalizedFullyConnected(NYC,5)
pos=nx.get_node_attributes(G,'pos')
print(pos)
nx.draw(G,pos,hold=None,node_size=10)
plt.show()
#print(G.nodes(data=true))'''