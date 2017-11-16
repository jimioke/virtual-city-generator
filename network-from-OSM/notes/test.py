import osmnx as ox
import networkx as nx
from file_paths import *
import query_osm as qr
from network import*


# G = nx.read_gpickle(GRAPH_FILE)
# G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
# G = ox.simplify_graph(G)
# ox.plot_graph(G)

def cutLineSegment(startCoord, endCoord, cutSize):
    vec = startCoord - endCoord
    segLenght = startCoord.dist(endCoord)
    return startCoord + (cutSize/segLenght * vec)

p = Coord(1,2)
p2 = Coord(1,4)
print(cutLineSegment(p, p2, 1))



[61327180, 61327071, 61327122]
[(61283300, 61283287), (61283345, 61283300), (61318589, 61329864), (61321123, 61322858), (61322858, 61322865), (61322865, 61283345), (61322874, 61328038), (61322877, 61322874), (61322880, 61322877), (61322884, 61322898), (61322888, 61322884), (61322898, 61323024), (61323024, 61327028), (61326955, 61322888), (61327028, 61322880), (61327071, 61327122), (61327094, 61318589), (61327122, 61327094), (61327122, 61320984), (61327180, 61327071), (61327276, 597845243), (61328038, 61328115), (61328087, 61326955), (61328115, 61328117), (61328117, 61331756), (61329864, 61328087), (61331756, 61321123), (597845243, 61327122)]


# def midpoint(pointA, pointB):
#     lonA = math.radians(pointA.x)
#     lonB = math.radians(pointB.x)
#     latA = math.radians(pointA.y)
#     latB = math.radians(pointB.y)
#
#     dLon = lonB - lonA
#
#     Bx = math.cos(latB) * math.cos(dLon)
#     By = math.cos(latB) * math.sin(dLon)
#
#     latC = math.atan2(math.sin(latA) + math.sin(latB),
#                   math.sqrt((math.cos(latA) + Bx) * (math.cos(latA) + Bx) + By * By))
#     lonC = lonA + math.atan2(By, math.cos(latA) + Bx)
#     lonC = (lonC + 3 * math.pi) % (2 * math.pi) - math.pi
#
#     return Point(math.degrees(lonC), math.degrees(latC))
