
from ipfn import *
import numpy as np


m = np.zeros((2,4,3))
m[0,0,0] = 1
m[0,0,1] = 2
m[0,0,2] = 1
m[0,1,0] = 3
m[0,1,1] = 5
m[0,1,2] = 5
m[0,2,0] = 6
m[0,2,1] = 2
m[0,2,2] = 2
m[0,3,0] = 1
m[0,3,1] = 7
m[0,3,2] = 2
m[1,0,0] = 5
m[1,0,1] = 4
m[1,0,2] = 2
m[1,1,0] = 5
m[1,1,1] = 5
m[1,1,2] = 5
m[1,2,0] = 3
m[1,2,1] = 8
m[1,2,2] = 7
m[1,3,0] = 2
m[1,3,1] = 7
m[1,3,2] = 6

print m

xipp = np.array([52, 48])
xpjp = np.array([20, 30, 35, 15])
xppk = np.array([35, 40, 25])
xijp = np.array([[9, 17, 19, 7], [11, 13, 16, 8]])
xpjk = np.array([[7, 9, 4], [8, 12, 10], [15, 12, 8], [5, 7, 3]])

aggregates = [xipp, xpjp, xppk, xijp, xpjk]
dimensions = [[0],[1],[2],[0,1],[1,2]]

IPF = ipfn(m, aggregates, dimensions)
m = IPF.iteration()
print xijp[0,0]
print m[0,0,:].sum()
print m


