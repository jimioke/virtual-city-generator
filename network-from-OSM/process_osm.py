import networkx as nx
import osmnx as ox
import time
from network import*

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

import query_osm as qr
from file_paths import *

SEGMENT_LOWER_BOUND = 20
# G = nx.read_gpickle(GRAPH_FILE)
G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
# ox.plot_graph(G)

# print(G.edges(data=True)[0:2])
# print(G.nodes(data=True)[0:2])

def getNodeTypes(G):
    sourceNodes = []
    sinkNodes = []
    mergingNodes = []
    divergingNodes = []
    intersectionNodes = []
    trafficLiNodes = []
    uniNodes = []

    for node, data in G.nodes(data=True):
        try:
            if data["trafficLid"] != 0:
                trafficLiNodes.append(node)
        except:
            pass
        outEdges = G.out_degree(node)
        inEdges = G.in_degree(node)
        neighbors = set(list(G.predecessors(node)) + list(G.successors(node)))
        num_neighbors = len(neighbors)
        d = G.degree(node)

        if node in neighbors:
            # self-loop
            intersectionNodes.append(node)
        elif inEdges == 0:
            sourceNodes.append(node)
        elif outEdges == 0:
            sinkNodes.append(node)
        elif num_neighbors==2 and (d==2 or d==4):
            uniNodes.append(node)
        elif inEdges == 2 and outEdges == 1:
            mergingNodes.append(node)
        elif inEdges == 1 and outEdges == 2:
            divergingNodes.append(node)
        else:
            intersectionNodes.append(node)
    return {'source':sourceNodes,
            'sink':sinkNodes,
            'uniNodes':uniNodes, # to be removed
            'merging': mergingNodes,
            'diverging': divergingNodes,
            'intersection':intersectionNodes,
            'trafficL':trafficLiNodes}

# Modified OSMnx method. We use our node_type function instead of is_endpoint.
def get_paths_to_simplify(G, uniNodesSet):
    """
    Create a list of all the paths to be simplified between endpoint nodes.

    The path is ordered from the first endpoint, through the interstitial nodes,
    to the second endpoint.

    Parameters
    ----------
    G : networkx multidigraph
    strict : bool
        if False, allow nodes to be end points even if they fail all other rules
        but have edges with different OSM IDs

    Returns
    -------
    paths_to_simplify : list
    """

    # first identify all the nodes that are endpoints
    start_time = time.time()
    endpoints = set([node for node in G.nodes() if not node in uniNodesSet])
    paths_to_simplify = []

    # for each endpoint node, look at each of its successor nodes
    for node in endpoints:
        for successor in G.successors(node):
            if successor not in endpoints:
                # if the successor is not an endpoint, build a path from the
                # endpoint node to the next endpoint node
                try:
                    path = ox.build_path(G, successor, endpoints, path=[node, successor])
                    paths_to_simplify.append(path)
                except RuntimeError:
                    print("RecursionError")
                    # recursion errors occur if some connected component is a
                    # self-contained ring in which all nodes are not end points
                    # handle it by just ignoring that component and letting its
                    # topology remain intact (this should be a rare occurrence)
                    # RuntimeError is what Python <3.5 will throw, Py3.5+ throws
                    # RecursionError but it is a subtype of RuntimeError so it
                    # still gets handled
    return paths_to_simplify

def build_linkGraph(G, uniNodesSet):
    """

    Create a link graph removing all nodes that are not intersections or dead-ends.
    Each edge (link) will have intersection or dead-end nodes.

    Parameters
    ----------
    G : graph

    Returns
    -------
    networkx multidigraph
    """

    linkGraph = G.copy()
    # linkGraph = nx.MultiDiGraph(name='linkGraoh', crs={'init':'epsg:4326'})
    all_nodes_to_remove = []
    all_edges_to_add = []

    # construct a list of all the paths that need to be simplified
    paths = get_paths_to_simplify(G, uniNodesSet)

    start_time = time.time()
    endsToPath = {}
    for path in paths:
        # path is a link that ends at intermediate nodes, e.g, intersection, source or sink node.
        # Collect intermediate edge attributes
        edge_attributes = {}
        all_edges = zip(path[:-1], path[1:])
        for u, v in all_edges:
            # each edge:
            # {'osmid': 8614961, 'oneway': True, 'lanes': '1', 'name': 'Pearl Street', 'highway': 'tertiary', 'width': '12.2', 'length': 72.679754393141266}

            # there shouldn't be multiple edges between interstitial nodes
            if not G.number_of_edges(u=u, v=v) == 1:
                # OSM data has multiple edges !!!
                print('Multiple edges between "{}" and "{}" found when merging path ends: '.format(u, v), level=lg.WARNING)

            # the only element in this list as long as above check is True
            # (MultiGraphs use keys (the 0 here), indexed with ints from 0 and
            # up)
            edge = G.edges[u, v, 0]
            for key in edge:
                # print(key, edge)
                if key in edge_attributes:
                    # if this key already exists in the dict, append it to the
                    # value list
                    edge_attributes[key].append(edge[key])
                else:
                    # if this key doesn't already exist, set the value to a list
                    # containing the one value
                    edge_attributes[key] = [edge[key]]

        # Combine intermediate edge attributes and build segments.
        for key in edge_attributes:
            # don't touch the length attribute, we'll sum it at the end
            if len(set(edge_attributes[key])) == 1 and not key == 'length':
                # if there's only 1 unique value in this attribute list,
                # consolidate it to the single value (the zero-th)
                edge_attributes[key] = edge_attributes[key][0]
            elif not key == 'length':
                # otherwise, if there are multiple values, keep one of each value
                edge_attributes[key] = list(set(edge_attributes[key]))

        # construct the geometry and sum the lengths of the segments
        edge_attributes['geometry'] = LineString([Point((G.nodes[node]['x'], G.nodes[node]['y'])) for node in path])
        edge_attributes['length'] = sum(edge_attributes['length'])
        # print(edge_attributes)
        # add the nodes and edges to their lists for processing at the end
        all_nodes_to_remove.extend(path[1:-1])
        all_edges_to_add.append({'origin':path[0],
                                 'destination':path[-1],
                                 'attr_dict':edge_attributes})
        endsToPath[(path[0], path[-1])] = path

    # for each edge to add in the list we assembled, create a new edge between
    # the origin and destination
    for edge in all_edges_to_add:
        linkGraph.add_edge(edge['origin'], edge['destination'], **edge['attr_dict'])
        # Graph

    # finally remove all the interstitial nodes between the new edges
    linkGraph.remove_nodes_from(set(all_nodes_to_remove))

    msg = 'Link graph (from {:,} to {:,} nodes and from {:,} to {:,} edges) in {:,.2f} seconds'
    print(msg.format(len(list(G.nodes())), len(list(linkGraph.nodes())), len(list(G.edges())), len(list(linkGraph.edges())), time.time()-start_time))
    return linkGraph, endsToPath

def constructNodesLinks(G, tempnodeDict):
    # TODO(complete the pseudo code)
    nodes = []
    links = []
    intersectionRadius = {'incoming':{}, 'outgoing':{}} # linkId: shortening
    link_id = 1
    endsToLinkId = {}
    for upnode, dnnode, data in G.edges(data=True):
        # TODO: road_type, category?
        link = Link(link_id, "EXPRESSWAY", "ROUNDABOUT", upnode, dnnode, data['name'])
        endsToLinkId[(upnode, dnnode)] = link_id
        link_id += 1
        links.append(link)

    for nodeId, data in G.nodes(data=True):
        nodeType = 0
        trafficLid = 0

        # TODO: use a set or get id to type dic (efficiency)
        if nodeId in tempnodeDict['intersection']:
            nodeType = 2
        elif nodeId in tempnodeDict['diverging'] or tempnodeDict['merging']:
            nodeType = 3
        elif nodeId in tempnodeDict['source'] or tempnodeDict['sink']:
            nodeType = 1

        try:
            if data["trafficLid"] != 0:
                trafficLiNodes.append(node)
        except:
            pass
        node = Node(nodeId, nodeType, trafficLid, data['x'], data['y'])
        nodes.append(node)

        # turning path radius for intersections
        if nodeType == 2:
            # TODO: handle missing width and lanes
            in_edges = [(endsToLinkId[(u,v)], data['width'], data['lanes']) for u,v,data in G.in_edges(nodeId, data=True)]
            out_edges = [(endsToLinkId[(u,v)], data['width'], data['lanes']) for u,v,data in G.in_edges(nodeId, data=True)]
            # links = node.neighbors [in_edges() and out_edges()]
            maxRadius = max([ float(edge[1]) * float(edge[2]) for edge in in_edges + out_edges])
            for linkId, _, _ in in_edges:
                intersectionRadius['incoming'][linkId] = maxRadius
            for linkId, _, _ in out_edges:
                intersectionRadius['outgoing'][linkId] = maxRadius

    return node, link, intersectionRadius, endsToLinkId
    # return None, None, None

# shortening and merging
def constructSegments(linkToPath, intersectionRadius):
    segments = []
    segToLink = {}
    linkToSeg = {}

    # for link, path in linkToPath.items():
    #     linkToSeg[link] = []
    #     if link['length'] < intersectionRadius['incoming'][link] + intersectionRadius['outgoing'][link]:
    #         print('too short link')
    #         pass
    #     all_edges = zip(path[:-1], path[1:])
    #     SEGMENT_SEQ_NUM = 0
    #     accumulated_segment_len = 0
    #     current_segment_len = 0
    #     current_index = 0
    #     segment_nodes = []
    #
    #     # Merge edges and create segments
    #     while current_index < len(all_edges):
    #         u, v = all_edges[current_index]
    #         edge = G.edges[u, v, 0]
    #         segment_nodes.append(v)
    #         current_segment_len += edge['length']
    #         accumulated_segment_len += edge['length']
    #         if current_segment_len >= SEGMENT_LOWER_BOUND:
    #             # Check if a set of the rest nodes is too short for a segment.
    #             if edge_attributes['length'] - accumulated_segment_len < SEGMENT_LOWER_BOUND:
    #                 # Combine all nodes into a segment.
    #                 create_segment(segment_nodes.append(all_edges[current_index+1:]))
    #                 break
    #             else:
    #                 create_segment(segment_nodes, SEGMENT_ID, LINK_ID, SEGMENT_SEQ_NUM)
    #                 segment_nodes = []
    #                 current_segment_len = 0
    #                 SEGMENT_ID += 1
    #                 SEGMENT_SEQ_NUM = 0
    #         current_index += 1
            # segment = Segment(id, link, sequence, num_lanes, capacity, speedlimit, tag, category, position, length)
            # segments.append(segment)
            # segToLink[id] = link
            # linkToSeg[link].append(segment)
        # return segments, segToLink, linkToSeg
    return None, None, None

def getLinkToPath(endsToLinkId, endsToPath):
    linkToPath = {}
    for ends, linkId in endsToLinkId.items():
        # has multiple nodes
        if ends in endsToPath:
            linkToPath[linkId] = endsToPath[ends]
        # else:
        #     linkToPath[ends] = 'singleton'
    return linkToPath

tempnodeDict = getNodeTypes(G)
linkGraph, endsToPath = build_linkGraph(G, set(tempnodeDict['uniNodes']))
nodes, links, intersectionRadius, endsToLinkId = constructNodesLinks(linkGraph, tempnodeDict)
linkToPath = getLinkToPath(endsToLinkId, endsToPath)

segments, segToLink, linkToSeg = constructSegments(linkToPath, intersectionRadius)



# print(linkGraph.edges(data=True))
# ox.plot_graph(G)
