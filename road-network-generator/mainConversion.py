from processing import*
from extraFunctions import*
from collections import OrderedDict


#inputFolder = "Inputs/Small3"
#inputFolder = "Inputs/GBAFull"
#inputFolder = "Inputs/GBAFullv3"
# inputFolder = "Inputs/Small1"
inputFolder = "Inputs/Santiago/mainConversion-Input/"

#inputFolder = "Inputs/Kat"
baseFname = os.path.join(inputFolder,"Base-shortened.csv")
baseAttFname = os.path.join(inputFolder,"Base-attributes.csv")
#baseAttFname = os.path.join(inputFolder,"subset.csv")
pointFname = os.path.join(inputFolder,"Points.csv")
connectFname = os.path.join(inputFolder,"Connections_Sumo.csv")
typeToWidthFname = os.path.join(inputFolder,"LinkCat_Roadtype_LaneWidth.csv")
ffsFname = os.path.join(inputFolder,"HCM2000.csv")

#==================================================================================================

def conv(s):
    try:
        s=float(s)
    except ValueError:
        pass
    return s

#==================================================================================================

def readData(baseFname,baseAttFname,pointFname):
    '''
    '''
    # reading base file
    basePoly = OrderedDict()
    with open(baseFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            id = row['ID']
            if id not in basePoly:
                basePoly[id] = []
            basePoly[id].append(row)

    # sort basePoly

    # reading base attributes
    baseAttributes = OrderedDict()
    with open(baseAttFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            baseAttributes[row['ID']] = row

    # reading points
    points = OrderedDict()
    with open(pointFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            points[row['nodeid']] = row
    #pdb.set_trace()

    # reading connectionss
    connSumo = OrderedDict()
    # with open(connectFname,'rb') as ifile:
    #     reader = csv.DictReader(ifile)
    #     count = 0
    #     for row in reader:
    #         connSumo[(row['from_lane'],row['to_lane'])] = row
    #         count += 1
    #     if count>len(connSumo):
    #         print "+++ @readData(): The data has multiple connections between the same pair of lanes"
    #         pdb_set_trace()
    return basePoly,baseAttributes,points,connSumo

#==================================================================================================


def main():
    '''
        The main function which runs the conversion script. It does the following
        1.
        2.

    '''
    print "The inputFolder is : ", inputFolder
    #---Reading all the data

    basePoly,baseAttributes,points,connSumo = readData(baseFname,baseAttFname,pointFname)
    print "------------------ Read all the data ------------------"

    #---Contructing the elements: links,segments,lanes,nodes
    segToLink,linkToSeg,tempnodeDict = segmentToLink(baseAttributes)
    print "----------Mapped segments to links and viceversa-------------"
    segments,links,linktts = constructSegmentsLinks(baseAttributes,basePoly,segToLink,linkToSeg,typeToWidthFname,ffsFname)
    nodes = constructNodes(links,points)
    lanes = constructLanes(segments,typeToWidthFname)
    print "----------Constructed segments,links,nodes, and lanes-------------"
    #---Processing the connections
    #connections = removeUTurns(connections)
    # connSumo = checkConnections(connSumo,baseAttributes,tempnodeDict,lanes) # TODO ERROR
    laneconnections,turninggroups = constructConnections(connSumo,nodes,links,segments,lanes,segToLink)

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
