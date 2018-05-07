################################################################################
# Module: simplify.py
# Description: Query OpenStreetMap and prepare SimMobility road network files.
# Written by: Iveel Tsogsuren, Arun Akkinepally
################################################################################
from collections import OrderedDict
import process_osm as posm
import osmnx as ox
import query_osm as qr
import networkx as nx
import os
from network import*
# from processing import*

LAT_LONG_CRS = {'init': 'epsg:4326'}
TEL_AVIV_CRS = {'init': 'epsg:2039'}

# Get default SimMobility attribute values
inputFolder = "metadata/"
typeToWidthFname = os.path.join(inputFolder,"LinkCat_Roadtype_LaneWidth.csv")
ffsFname = os.path.join(inputFolder,"HCM2000.csv")

# Set this directory where you optionally pass boundary.shp file and get all outputs.
directory = '/Outputs/Tel_Aviv'
directory = '/Outputs/Tel_Aviv_drive_all'
directory = '/Outputs/Tel_Aviv_drive_main'
# boundary = os.getcwd() + '/Outputs/Tel_Aviv/Tel_Aviv_Metro_Area/buffer_wgs84.shp' # Can be either bounding box coordinates or
directory = '/Outputs/Test'
boundary = [42.3645,42.3635,-71.1046,-71.108]


# Prepare subfolders for outputs
outDir = os.getcwd() + directory
simmobility_crs_projected = outDir + "/simmobility_crs_projected"  # For later use.
simmobility_dir = outDir + "/simmobility_wgs84"
shapefile_dir = outDir + "/shapefiles"
sumo_dir = outDir + "/sumo"
graph_pickle_file = outDir + '/osm_graph.pkl'
for d in [outDir, simmobility_dir, simmobility_crs_projected, shapefile_dir, sumo_dir]:
    if not os.path.exists(d):
        print(d)
        os.makedirs(d)

def query_OSM(directory, boundary, graph_pickle_file, query='drive_main'):
    """
    Query OpenStreetMap and save it as a pickle file.

    Parameters
    ----------
    directory : directory path where inputs and outputs should be
    boundary : Boundary for road network which can be either polygon boundary file
               or bounding box coordinates [north, south, west, east]
    network_type : string
        {'walk', 'bike', 'drive_all', 'drive_main', 'drive_main_links_included', 'drive_service', 'all', 'all_private', 'none'}
        what type of street or other network to get
    """
    if type(boundary) == str: # boundary .shp file path
        polygon = gpd.read_file(boundary)
        polygon = polygon.get_value(0, 'geometry')
        mainG = ox.graph_from_polygon(polygon, network_type=query,  simplify=False, retain_all=True, truncate_by_edge=False)
    else: # bounding box []
        mainG = qr.graph_from_bbox(*boundary)
    nx.write_gpickle(mainG, graph_pickle_file)

def main(graph_pickle_file=graph_pickle_file, simmobility_dir=simmobility_dir):
    """
    Create all SimMobility road network tables and their shapes given a OSM graph file.

    Parameters
    ----------
    graph_pickle_file : file path of OSM graph in pickle format.
    simmobility_dir : output directory
    """
    query_OSM(directory, boundary, graph_pickle_file)
    # all SimMobility road network module files.
    mainG = nx.read_gpickle(graph_pickle_file)
    roadnetwork = Network(mainG)
    roadnetwork.process_segments_links_nodes(clean_intersections=False)
    roadnetwork.lanes = posm.constructLanes(roadnetwork.segments, typeToWidthFname)
    roadnetwork.constructSegmentConnections()
    roadnetwork.construct_default_turning_path()

    # Files for creating smart turnning path connections using SUMO. TODO: use SUMO.
    # roadnetwork.writeSumoShapefile(sumo_dir)
    # roadnetwork.construct_turning_paths_from_SUMO(sumo_dir)

    roadnetwork.write_wgs84(foldername=simmobility_dir+inputFolder.split('/')[1])
    roadnetwork.writeShapeFiles(foldername=shapefile_dir+inputFolder.split('/')[1])

main()
