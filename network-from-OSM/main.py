from processing import*
from extraFunctions import*
from collections import OrderedDict
import process_osm as posm
import query_osm as qr

inputFolder = "metadata/"
typeToWidthFname = os.path.join(inputFolder,"LinkCat_Roadtype_LaneWidth.csv")
ffsFname = os.path.join(inputFolder,"HCM2000.csv")

def main():
    print "------------------ Query osm data ------------------"
    G = qr.graph_from_bbox(42.3641,42.3635,-71.1046,-71.1034)
    tempnodeDict = posm.getNodeTypes(G)
    linkGraph = posm.build_linkGraph(G, set(tempnodeDict['uniNodes']))
    posm.mergeClusteringIntersection(linkGraph)
    nodes, links = posm.constructNodesLinks(linkGraph, G, tempnodeDict)
    segments, segToLink, linkToSeg = posm.constructSegments(linkGraph, G)
    linktts = posm.setLinkSegmentAttr(segments, links, linkToSeg)

    connSumo = OrderedDict() # TODO: create lane connections
    # TODO: linktts, connSumo

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
    net.write(foldername='Outputs/'+inputFolder.split('/')[1])

    nodeLinks = set([item.upnode for k,item in links.iteritems()] + [item.dnnode for k,item in links.iteritems()])
    nodeNode = set(nodes.keys())

    # pdb.set_trace()

#---Making required directories
if not os.path.exists("Corrections"):
    os.makedirs("Corrections")
if not os.path.exists("Output"):
    os.makedirs("Output")

main()
