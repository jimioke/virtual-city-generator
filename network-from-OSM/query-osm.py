import osmnx as ox
import networkx as nx
import json

def graph_from_bbox(north, south, east, west, network_type='drive',
                    retain_all=False, truncate_by_edge=False,
                    timeout=180, memory=None,
                    max_query_area_size=50*1000*50*1000,
                    infrastructure='way["highway"]'):
    """
    Create a networkx graph from OSM data within some bounding box.

    Parameters
    ----------
    north : float
        northern latitude of bounding box
    south : float
        southern latitude of bounding box
    east : float
        eastern longitude of bounding box
    west : float
        western longitude of bounding box
    network_type : string
        what type of street network to get
    simplify : bool
        if true, simplify the graph topology
    retain_all : bool
        if True, return the entire graph even if it is not connected
    truncate_by_edge : bool
        if True retain node if it's outside bbox but at least one of node's
        neighbors are within bbox
    name : string
        the name of the graph
    timeout : int
        the timeout interval for requests and to pass to API
    memory : int
        server memory allocation size for the query, in bytes. If none, server
        will use its default allocation size
    max_query_area_size : float
        max size for any part of the geometry, in square degrees: any polygon
        bigger will get divided up for multiple queries to API
    clean_periphery : bool
        if True (and simplify=True), buffer 0.5km to get a graph larger than
        requested, then simplify, then truncate it to requested spatial extent
    infrastructure : string
        download infrastructure of given type (default is streets (ie, 'way["highway"]') but other
        infrastructures may be selected like power grids (ie, 'way["power"~"line"]'))

    Returns
    -------
    networkx multidigraph
    """

    # get the network data from OSM
    response_jsons = ox.osm_net_download(north=north, south=south, east=east,
                                      west=west, network_type=network_type,
                                      timeout=timeout, memory=memory,
                                      max_query_area_size=max_query_area_size,
                                      infrastructure=infrastructure)

    G = ox.create_graph(response_jsons, retain_all=retain_all, network_type=network_type)
    # with open('json_osm.txt', 'w') as outfile:
    #     json.dump(response_jsons, outfile)
    return G

# G = graph_from_bbox(42.3671,42.3627,-71.1064,-71.0978) #380 nodes and 562 edges
# G = graph_from_bbox(42.3645,42.3635,-71.1046,-71.1028) #44 nodes and 43 edges
G = graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034) #29 nodes and 28 edges

# Investigate the graph
# print(G.edges(data=True)[0:2])
# print(G.nodes(data=True)[0:2])
# ox.plot_graph(G)

nx.write_gpickle(G, 'graph.gpickle')
