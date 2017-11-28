from collections import OrderedDict
import process_osm as posm
import query_osm as qr
import networkx as nx
import os
from network import*
# from processing import*

inputFolder = "metadata/"
# outputFolder = "/Outputs/Philadelphia_sumo"

# Ten prototype cities
# outputFolder = "/Outputs/Charlotte_default_turning_paths"
# outputFolder = "/Outputs/Madrid_default_turning_paths"
# outputFolder = "/Outputs/Vancouver_default_turning_paths"
# outputFolder = "/Outputs/Bandung_default_turning_paths"
# outputFolder = "/Outputs/Lagos_default_turning_paths"
# outputFolder = "/Outputs/Hiroshima_default_turning_paths"
# outputFolder = "/Outputs/Isfahan_default_turning_paths"
# outputFolder = "/Outputs/Mashhad_default_turning_paths"
# outputFolder = "/Outputs/Tehran_default_turning_paths"
# outputFolder = "/Outputs/Dalian_default_turning_paths"
# outputFolder = "/Outputs/smallBoston"
outputFolder = "/Outputs/test"
outputFolder = "/Outputs/Baltimore"

# Output and temp dir
outDir = os.getcwd() + outputFolder
simmobility_dir = outDir + "/simmobility"
shapefile_dir = outDir + "/shapefiles"
sumo_dir = outDir + "/sumo"
# outputFolder = "/Outputs/Singapore/"
typeToWidthFname = os.path.join(inputFolder,"LinkCat_Roadtype_LaneWidth.csv")
ffsFname = os.path.join(inputFolder,"HCM2000.csv")


def main():
    print "------------------ Query osm data to ouptutfolder: {}------------------".format(outputFolder)
    # mainG = qr.graph_from_bbox(40.1035,39.9009,-74.9870,-75.2503) # Philadelphia
    # mainG = qr.graph_from_bbox(40.0318,39.9387,-75.1231,-75.1966) # Philadelphia smaller
    # mainG = qr.graph_from_bbox(31.2086,30.3237,104.6074,103.3088) # Chendu, China
    # mainG = qr.graph_from_bbox(38.8370, 38.4692, -90.0247, -90.4635) # St. Louis
    # mainG = qr.graph_from_bbox(1.4459, 1.2633, 104.0309, 103.6409) # Singapore
    # G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
    # nx.write_gpickle(G, 'Outputs/Philadelphia/Philadelphia_graph.gpickle')

    # Ten prototype cities
    # mainG = qr.graph_from_bbox(35.3779, 35.0514, -80.6039, -81.0022) # Charlotte
    # mainG = qr.graph_from_bbox(40.5357, 40.3068, -3.5403, -3.8974) # Madrid
    # mainG = qr.graph_from_bbox(49.3009, 49.2032, -123.0180, -123.2666) # Vancouver
    # mainG = qr.graph_from_bbox(-6.8274, -7.0417, 107.7683, 107.4408) # Bandung
    # mainG = qr.graph_from_bbox(6.5296, 6.3801, 3.4923, 3.2389) # lagos
    # mainG = qr.graph_from_bbox(34.6274, 34.2731, 132.7354, 132.1092) # Hiroshima
    # mainG = qr.graph_from_bbox(32.7988, 32.4959, 51.9283, 51.3824) # Isfahan
    # mainG = qr.graph_from_bbox(36.5869, 36.0069, 60.1515, 59.0598) # Mashhad
    # mainG = qr.graph_from_bbox(35.8445, 35.5523, 51.6206, 51.0748) # Tehran
    # mainG = qr.graph_from_bbox(39.2003, 38.6405, 122.1844, 121.0927) # Dalian
    # mainG = qr.graph_from_bbox(-71.090201,42.358556,-71.077083,42.366463) # Boston small
    # mainG = qr.graph_from_bbox(42.3729, 42.3579, -71.0750, -71.1052)
    # mainG = qr.graph_from_bbox(39.4362, 39.1492, -76.3770, -76.8810) # Baltimore



    # mainG = qr.graph_from_bbox(42.3671,42.3627,-71.1064,-71.0978) #380 nodes and 562 edges
    # mainG = qr.graph_from_bbox(42.3645,42.3635,-71.1046,-71.1028) #44 nodes and 43 edges
    mainG = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)

    # mainG = qr.graph_from_place('Los Altos, CA, USA')
    roadnetwork = Network(mainG)
    roadnetwork.process_segments_links_nodes()
    roadnetwork.lanes = posm.constructLanes(roadnetwork.segments, typeToWidthFname)

    roadnetwork.constructSegmentConnections()
    roadnetwork.construct_default_turning_path()

    roadnetwork.writeSumoShapefile(sumo_dir)
    # roadnetwork.construct_turning_paths_from_SUMO(sumo_dir)

    roadnetwork.write(foldername=simmobility_dir+inputFolder.split('/')[1])
    roadnetwork.writeShapeFiles(foldername=shapefile_dir+inputFolder.split('/')[1])

#---Making required directories
# directory of script
for d in [outDir, simmobility_dir,shapefile_dir, sumo_dir]:
    if not os.path.exists(d):
        os.makedirs(d)
main()
