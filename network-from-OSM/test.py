import osmnx as ox
import networkx as nx
from file_paths import *
import query_osm as qr


# G = nx.read_gpickle(GRAPH_FILE)
G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
G = ox.simplify_graph(G)
ox.plot_graph(G)
