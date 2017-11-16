from processing import*
from extraFunctions import*
from collections import OrderedDict
import process_osm as posm
import query_osm as qr
import networkx as nx

inputFolder = "metadata/"
outputFolder = "Outputs/Philadelphia/"
typeToWidthFname = os.path.join(inputFolder,"LinkCat_Roadtype_LaneWidth.csv")
ffsFname = os.path.join(inputFolder,"HCM2000.csv")

def main():
    print "------------------ Query osm data ------------------"
    mainG = qr.graph_from_bbox(40.1035,39.9009,-74.9870,-75.2503) # Philadelphia
    # G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
    # nx.write_gpickle(G, 'Outputs/Philadelphia/Philadelphia_graph.gpickle')

    # G = qr.graph_from_bbox(42.3671,42.3627,-71.1064,-71.0978) #380 nodes and 562 edges
    # G = qr.graph_from_bbox(42.3645,42.3635,-71.1046,-71.1028) #44 nodes and 43 edges
    # G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
    tempnodeDict = posm.getNodeTypes(mainG)
    mainLinkGraph = posm.build_linkGraph(mainG, set(tempnodeDict['uniNodes']))
    posm.mergeClusteringIntersection(mainLinkGraph)
    nodes, links = posm.constructNodesLinks(mainLinkGraph, mainG, tempnodeDict)
    segments, segToLink, linkToSeg = posm.constructSegments(mainLinkGraph, mainG)
    linktts = posm.setLinkSegmentAttr(segments, links, linkToSeg)

    connSumo = OrderedDict() # TODO: create lane connections
    # TODO: linktts, connSumo

    # connections,turninggroups,conncount = constructTurningPathsAll(nodes,links,segments,connections,lanes,conncount)

    print "----------Mapped segments to links and viceversa-------------"
    # segments,links,linktts = constructSegmentsLinks(baseAttributes,basePoly,segToLink,linkToSeg,typeToWidthFname,ffsFname)
    lanes = constructLanes(segments,typeToWidthFname)

    print "----------Constructed segments,links,nodes, and lanes-------------"
    #---Processing the connections
    #connections = removeUTurns(connections)
    # connSumo = checkConnections(connSumo,baseAttributes,tempnodeDict,lanes) # TODO ERROR
    laneconnections,turninggroups = constructConnections(connSumo,nodes,links,segments,lanes,segToLink) # TODO ERROR

    print "----------Constructed connections-------------" # DONE Iveel
    laneconnections = processAndAddConnections(nodes,tempnodeDict,links,segments,lanes,laneconnections,turninggroups,segToLink)

    net = Network(nodes,links,segments,lanes,laneconnections,turninggroups,linktts)
    net.write(foldername=outputFolder+'/simmobility'+inputFolder.split('/')[1])
    # net.writeShapeFiles(foldername=outputFolder+'/shapefiles'+inputFolder.split('/')[1])

    # nodeLinks = set([item.upnode for k,item in links.iteritems()] + [item.dnnode for k,item in links.iteritems()])
    # nodeNode = set(nodes.keys())

    # pdb.set_trace()

#---Making required directories
if not os.path.exists("Corrections"):
    os.makedirs("Corrections")
if not os.path.exists("Output"):
    os.makedirs("Output")

main()
