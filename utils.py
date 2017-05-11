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
from scipy.spatial import cKDTree

def graphMatricesToAdjandShortestPath(graphs,normgraphs):
    '''
    Input: 
    Graphs = List of graphs (originals)
    Normgraphs = List of normalized graphs (new)
    
    Output:
    Adjmat = Upper Triangle of Ajacency Matrix from all original graphs (converted to unidirectional)
    ShortestPathmat = Upper Triangle of Shortest Path Matrix from new normalized matrix
    '''
    adjmat = []
    shortestpathmat = []
    total_length = 0
    for g in range(0,len(graphs)):
        adj = getAdjacencyDataFrame(graphs[g].to_undirected())
        adj = adj.where(np.tril(np.ones(adj.shape),k=-1).astype(np.bool))
        adj = adj.stack().reset_index()
        adj.columns = ['OSMID1','OSMID2','Adj']
        #adj.loc[adj.value>1,'Value']=1

        #print(adj)
        shortpath = getShortestPathDataFrame(normgraphs[g])
        #print(shortpath)
        shortpath = shortpath.where(np.tril(np.ones(shortpath.shape),k=-1).astype(np.bool))
        shortpath = shortpath.stack().reset_index()
        shortpath.columns = ['Row','Column','Shortpath']

        
        print('g',g)

        shortestpathmat.append(shortpath)
        adjmat.append(adj)
        x, y = adj.shape
        total_length+=x
    
    return adjmat, shortestpathmat, total_length

def getShortestPathX(g):
    df = getShortestPathDataFrame(g)
    # print(shortpath[0])
    # print(pd.melt(shortpath))
    # #pd.melt(shortpath, id_vars=['A'], value_vars=['B'])
    # r,c = shortpath.shape
    # ind = np.triu_indices(r,k=1)
    # shortpath = shortpath.values[ind].flatten()[:,np.newaxis]

    df = df.where(np.tril(np.ones(df.shape),k=-1).astype(np.bool))
    df = df.stack().reset_index()
    df.columns = ['Row','Column','Shortpath']

    return df

def getEuclideanDistanceX(g):
    df = getActualDistanceDataFrame(g)
    df = df.where(np.tril(np.ones(df.shape),k=-1).astype(np.bool))
    df = df.stack().reset_index()
    df.columns = ['Row','Column','Dist']

    return df



def CreateFullyConnectedGraph(lat,longitude,samples,k):
    '''
    Input:
    Lat/Longitude Matrices from input graphs
    samples - the number of samples from the distribution
    k-1 - k nearest neighbors

    Output:
    nog = Node-only graph
    fcg = Fully connected graph
    '''

    kde = getKernelDensity(lat,longitude)

    redrawsk = kde.sample(n_samples=samples)
    points = np.matrix(redrawsk)
    #points = np.square(points)
    #print(points)


    nog = nx.Graph()
    fcg = nx.Graph()

    keys = np.arange(samples).reshape(samples,1)

    comb = np.concatenate((keys,points),axis=1)

    r, c = np.shape(comb)
    print(np.shape(comb))
    #print('comb',comb)

    for i in range (0, r):
        nog.add_node(comb[i,0], pos=(comb[i,1],comb[i,2]), x=comb[i,1], y=comb[i,2])
        fcg.add_node(comb[i,0], pos=(comb[i,1],comb[i,2]), x=comb[i,1], y=comb[i,2])
    
    nn = np.zeros(shape=[r,k*2])
    tree = cKDTree(points, leafsize=1000000)
    i=0
    for item in points:
        res = tree.query(item, k=k)
        nn[i] = np.concatenate((res[0],res[1]), axis=1)
        i+=1
    
    #connect k-1 nearest edges
    for j in range (0, r):
        for l in range (k+1, (k*2)):
            if( fcg.has_edge(nn[j,k],nn[j,l])==False):
                fcg.add_edge(nn[j,k],nn[j,l], dist=nn[j,l-k])

    
    return nog, fcg


def transformGraphToNormalizedFullyConnected(G,k):
    '''
    Input: Graph G of a city
    Output:
    GN: undirected graph with normalized lat/long w/ (k-1)-nearest neighbors connected
    '''
    #get node data frame
    nodedataframe = getNodeDataFrame(G)

    #get length of data frame
    nodecount = len(nodedataframe.index)

    #create empty normalize lat/long matrices
    lat,longitude = getNormalizedLatLongs(nodedataframe)

    #create blank non-directional graph object
    GN = nx.Graph()

    points = np.concatenate((lat,longitude),axis=1)
    keys = np.arange(nodecount).reshape(nodecount,1)
    comb = np.concatenate((keys,points),axis=1)
    #fill new graph with nodes and normalized lat/long
    for i in range (0,nodecount):
        GN.add_node(comb[i,0], pos=(comb[i,1],comb[i,2]), x=comb[i,1], y=comb[i,2])
    
    #run a kdtree to find k nearest points and then pull out distances
    nn = np.zeros(shape=[nodecount,k*2])
    tree = cKDTree(points, leafsize=1000000)
    i=0
    for item in points:
        res = tree.query(item, k=k)
        nn[i] = np.concatenate((res[0],res[1]))
        i+=1
    
    #connect k-1 nearest edges
    for j in range (0, nodecount):
        for l in range (k+1, (k*2)):
            if( GN.has_edge(nn[j,k],nn[j,l])==False):
                GN.add_edge(nn[j,k],nn[j,l], dist=nn[j,l-k])


    return GN

#gets the graph of a particular location
def getGraph(location, type='drive'):
	# gdf = ox.gdf_from_place(location)
	# areaSqM = ox.project_gdf(gdf).unary_union.area
	try:
		G = ox.graph_from_place(location, network_type='drive')
		#ox.plot_graph(ox.project_graph(G))
	except ValueError:
		G = ox.graph_from_place(location, network_type='drive',which_result=2)
	return G #, areaSqM

#normalize latitude and longitude coordinates based on average, essentially create a coordinate system
#centered at the centroid of the town or city, all referenced from 0,0 rather than the equator
#takes in a node matrix and returns the normalized latitude and longitude

def getNormalizedLatLongs(NodeMatrix):
    xbar = np.average(NodeMatrix['x'])
    ybar = np.average(NodeMatrix['y'])

    normalizedx = NodeMatrix['x']-xbar
    normalizedy = NodeMatrix['y']-ybar

    normalizedx = normalizedx[:,np.newaxis]
    normalizedy = normalizedy[:,np.newaxis]

    return normalizedx, normalizedy

def getNormalizedLatLongsMatrix(NodeMatrix):
    nodeid = NodeMatrix[0]
    x = NodeMatrix['x']
    y = NodeMatrix['y']
    norm_matrix = np.column_stack([nodeid,x,y])

    return norm_matrix

#returns the adjacency matrix as a pandas dataframe
def getAdjacencyDataFrame(G):
    return nx.to_pandas_dataframe(G)

#returns the distance matrix in (double check this!) meters; 
#note distances only reported when nodes are connected by edges
def getActualDistanceDataFrame(G):
    distancematrix = getAdjacencyDataFrame(G)
    edges = G.edges(data=True)
    for x in range(0,edges.__len__()):
        distancematrix[edges[x][0]][edges[x][1]] = edges[x][2]['dist']
    
    return distancematrix

#returns the shortest paths distance matrix between all nodes
def getShortestPathDataFrame(G):
    shortestpaths = nx.all_pairs_shortest_path_length(G)
    shortestpathsmatrix = pd.DataFrame(shortestpaths)

    return shortestpathsmatrix

#takes in a file name and returns a graph object
def loadGraph(FileName):
    G = nx.read_gpickle(FileName+".gpickle")
    return G

#takes in a graph and saves a file, no return
def saveGraph(G, FileName):
    nx.write_gpickle(G, FileName+".gpickle")

#returns the node matrix
def getNodeDataFrame(G):
    gn = pd.DataFrame.from_dict(G.nodes(data=True))
    gn = pd.concat([gn,pd.DataFrame(gn[1].tolist())],axis=1)
    gn = gn.drop(1,axis=1)
    return gn

#create a kernel density function from x,y (e.g. lat/long)
#https://gist.github.com/daleroberts/7a13afed55f3e2388865b0ec94cd80d2

def getKernelDensity(x, y):
    # Calculate the point density
    xy = np.hstack([x,y])
    print('xyshape',xy.shape)
    d = xy.shape[0]
    n = xy.shape[1]
    #bw = (n * (d + 2) / 4.)**(-1. / (d + 4)) # silverman
    bw= .0026724137931034486
    print('bw',bw)
    #bw=.2
    # from sklearn.grid_search import GridSearchCV
    # grid = GridSearchCV(KernelDensity(),
    #                     {'bandwidth': np.linspace(0.0005, .005, 30)},
    #                     cv=20) # 20-fold cross-validation
    # grid.fit(xy)
    # print(grid.best_params_)

    kernel = KernelDensity(bandwidth=bw,metric='euclidean',
                            kernel='gaussian', algorithm='ball_tree')
    kernel.fit(xy)

    return kernel


#http://stackoverflow.com/questions/15736995/how-can-i-quickly-estimate-the-distance-between-two-latitude-longitude-points
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km








