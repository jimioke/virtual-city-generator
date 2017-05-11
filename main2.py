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
    #print(getNodeDataFrame(normfullconnectgraphs[g]))

#get lat/long matrix
dfstart = getNodeDataFrame(normfullconnectgraphs[0])
lat = dfstart['x'].values[:,np.newaxis]
longitude = dfstart['y'].values[:,np.newaxis]
for g in range(1,len(graphs)):
    df = getNodeDataFrame(normfullconnectgraphs[g])
    lat = np.concatenate((lat, df['x'].values[:,np.newaxis]))
    longitude = np.concatenate((longitude, df['y'].values[:,np.newaxis]))

#print('latshape',lat.shape)
#print('longshape',longitude)
#sample from distribution to create town with X points
nodesamplesize = 500 ## to be replaced
nog,fcg = CreateFullyConnectedGraph(lat,longitude,nodesamplesize,10)
#print(getNodeDataFrame(fcg))
#print(getActualDistanceDataFrame(fcg))
#get adjacencies and shortest path matrices
adj, short, total_length = graphMatricesToAdjandShortestPath(graphs,normfullconnectgraphs)

#create one long vector for X and Y
eucliddist = getEuclideanDistanceX(normfullconnectgraphs[0])
temp1 = pd.concat([adj[0], short[0]], axis=1)
df2 = pd.merge(temp1, eucliddist, on=['Row','Column'], how='inner')

for g in range (1,len(graphs)):
    e = getEuclideanDistanceX(normfullconnectgraphs[g])
    t = pd.concat([adj[g], short[g]], axis=1)
    df = pd.merge(t, e, on=['Row','Column'], how='inner')
    df2 = df2.append(df)
#print('euclid',eucliddist)
#print('df2',df2)
#print(df2.shape)

mat = df2.as_matrix()
#print(mat.shape)
btw = np.where((mat[:,6] > 0))
mat = mat[btw]
#print(mat.shape)
isnan = np.where(np.isnan(mat[:,5]) == False)
mat = mat[isnan]
#print(mat.shape)

X = mat[:,[5,6]]
Y = mat[:,2]
Y[Y>1]=1
#print(X.shape)
#print(Y.shape)
#print(np.sum(Y))

#print(X)


# In[7]:

clf = linear_model.LogisticRegression(C=1e5,max_iter=1000)
clf.fit(X, Y)
print('score',clf.score(X,Y))

#test = X[:,:]
#print(test)
#predictions = clf.predict_proba(test)
#print(np.average(predictions[:,1]))
#great = np.where(predictions[:,1]>.5)
#print(predictions[great])
#print(predictions[great].shape)


# In[13]:

fcgsp = getShortestPathX(fcg)
print('fcg shape unique',np.unique(fcgsp.as_matrix()[:,0]).shape)
gcpdist = getEuclideanDistanceX(fcg)
#getActualDistanceDataFrame(fcg).to_csv('gcpdist2.csv')
print('gcp shape unique',np.unique(gcpdist.as_matrix()[:,0]).shape)
dftest = pd.merge(fcgsp, gcpdist, on=['Row','Column'], how='inner')
print('dftest shape unique',np.unique(dftest.as_matrix()[:,0]).shape)
#print(dftest)

mid = dftest.as_matrix()
#print(mid.shape)
print('shape mid unique',np.unique(mid[:,0]).shape)
btwm = np.where((mid[:,3] > 0.0000000))
mid = mid[btwm]
print('shape mid unique',np.unique(mid[:,0]).shape)
print('mid',mid)
#print(mid.shape)
isnan = np.where(np.isnan(mid[:,2]) == False)
mid = mid[isnan]
print('shape mid unique',np.unique(mid[:,[0,1]]).shape)
#print(mid.shape)




predictions = clf.predict_proba(mid[:,[2,3]])

#print(mid, predictions)
print(mid.shape, predictions.shape)
final = np.concatenate((mid,predictions),axis=1)
#print(final)
# In[9]:

r,c = final.shape
#add most likely edge for each node
#for i in range (0,r):
#    iter=0
#    for j in range (0,r):
#        if( nog.has_edge(final[j,0],final[j,1])==False and iter<=0 and nog.number_of_edges(final[j,0])<=1):
#            nog.add_edge(final[j,0],final[j,1], origshortpath=final[j,2])
#            iter+=1

#while all nodes not connected to at least one other & no shortest path n/as & edge density <= distribution draw
edgedensity = .007 ## to be replaced by distribution draw
maxdegree = 8
iter=0
while True:
    if (nx.density(nog) >= edgedensity and np.min(pd.DataFrame.from_dict(nog.degree(), orient='index').as_matrix()) >= 1) and iter>1350:
        break ##add in shortest path condition)
    nodeiter = np.random.choice(np.arange(0,nodesamplesize),size=nodesamplesize)
    #print(nodeiter)
    for n in nodeiter:
        pe1 = np.where(final[:,1] == n)
        pe2 = np.where(final[:,0] == n)
              
        pedges1 = final[pe1]
        pedges2 = final[pe2]

        pedgefinal = np.concatenate((pedges1,pedges2))

        itertest = 0
        while nog.degree(n) == 0:
            choice = pedgefinal[np.random.choice(np.arange(0,pedgefinal.shape[0])), :]
            prob = np.random.random_sample()
            itertest+=1
            if itertest > 100:
                nog.add_edge(choice[0],choice[1], origshortpath=choice[2], dist=choice[3])
                iter+=1
                print(iter)

            #print('choice',choice)
            if (choice[5]>=prob):
                if nog.has_edge(choice[0],choice[1])==False:
                    if nog.degree(choice[0]) <= 4:
                        nog.add_edge(choice[0],choice[1], origshortpath=choice[2], dist=choice[3])
                        iter+=1
                        print(iter)

        choice = pedgefinal[np.random.choice(np.arange(0,pedgefinal.shape[0])), :]
        prob = np.random.random_sample()
        #print('choice',choice)
        if (choice[5]>=prob):
            if nog.has_edge(choice[0],choice[1])==False:
                if nog.degree(choice[0]) <= 4:
                    nog.add_edge(choice[0],choice[1], origshortpath=choice[2], dist=choice[3])
                    iter+=1
                    print(iter)

                    #print(1)

saveGraph(nog,'nogtest2')

pos=nx.get_node_attributes(nog,'pos')
nx.draw(nog,pos,hold=None,node_size=10)
plt.show()


pos=nx.get_node_attributes(fcg,'pos')
nx.draw(fcg,pos,hold=None,node_size=10)
plt.show()


# In[ ]:



