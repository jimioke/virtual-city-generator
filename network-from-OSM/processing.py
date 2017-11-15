import networkx as nx
import numpy as np
import csv,pdb,os,itertools,copy,math
from collections import OrderedDict
from numpy.linalg import norm
from network import *
from extraFunctions import *

outputFolder = "Output"
errorFolder = "Corrections"

#=================================================================================================

def getHCMSpeeds(filename):
    '''
        reads the HCM csv and returns a dictionary; check for duplicate keys
    '''
    ffsFunc = {}
    with open(filename,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for aRow in reader:
            #print aRow
            key = (aRow['LinkCat'],aRow['NumLane'],int(aRow['Capacity_vphPerLane']))
            assert key not in ffsFunc
            ffsFunc[key] = int(aRow['Speed_kmph'])
    return ffsFunc



#==================================================================================================


def getFfs(LinkCat,numLanes,capacity,ffsFunc):
    '''
        returns the closed ffs from the HCM values in ffsFunc
        noet that input capacity is total one
    '''
    if numLanes < 4:
        adict = {k:v for k,v in ffsFunc.iteritems() if k[0]==LinkCat and k[1]==str(numLanes)}
    else:
        adict = {k:v for k,v in ffsFunc.iteritems() if k[0]==LinkCat and k[1]=='3+'}

    capacities = [k[2] for k in adict]
    closeCap = min(capacities, key=lambda x:abs(x-capacity/numLanes))

    if numLanes < 4:
        return ffsFunc[(LinkCat,str(numLanes),closeCap)]
    else:
        return ffsFunc[(LinkCat,'3+',closeCap)]




#==================================================================================================

def checkConnections(connAttributes,baseAttributes,tempnodeDict,lanes):
    '''
        Checks the connections so that they meet SimMobility's requirements
    '''

    # Getting the list of lanes that have no downstream connections or no upstream connections (and are not connected to source or sink nodes)
    connList = connAttributes.keys()  # a list of all connections (fromlane,tolane)
    laneswithDwConn = set([item[0] for item in connList])  # lanes with downstream connections
    laneswithUpConn = set([item[1] for item in connList])  # lanes with upstream connections

    connLanes = laneswithDwConn.union(laneswithUpConn)
    laneSet = set([lane for lane in lanes])
    nonExistentLanes = list(connLanes - laneSet) # the set of lanes which are in conn but not in networks


    laneswithoutDwConn, laneswithoutUpConn = set(),set()
    totNumLanes = 0
    totLaneList = set()
    for id,section in baseAttributes.iteritems():
        numLanes = int(section['NB_LANES'])
        tnode,hnode = section['FNODE'],section['TNODE']
        totNumLanes += numLanes
        laneList = [str((int(section['ID'])*100)+i) for i in range(numLanes)] # getting the list of lanes in this section
        totLaneList.update(laneList)

        #---Getting the lanes that are not connected to sink (source) node and no downstream (upstream) connection
        for lane in laneList:
            if lane not in laneswithDwConn and hnode not in tempnodeDict['sink']:
                laneswithoutDwConn.add(lane)
            if lane not in laneswithUpConn and tnode not in tempnodeDict['source']:
                laneswithoutUpConn.add(lane)

    print "Checked lane connections..."
    #---Writing the cases to a file
    laneswithoutDwConn = list(laneswithoutDwConn)
    laneswithoutUpConn = list(laneswithoutUpConn)
    a = laneswithDwConn - totLaneList.intersection(laneswithDwConn)
    b = laneswithUpConn - totLaneList.intersection(laneswithUpConn)
    shadyLanes = list(a)+list(b)

    np.savetxt(os.path.join(errorFolder,'laneswithoutDwConn.txt'),laneswithoutDwConn,fmt='%s')
    np.savetxt(os.path.join(errorFolder,'laneswithoutUpConn.txt'),laneswithoutUpConn,fmt='%s')
    np.savetxt(os.path.join(errorFolder,'nonExistentLanes.txt'),nonExistentLanes,fmt='%s')
    np.savetxt(os.path.join(errorFolder,'shadyLanes.txt'),shadyLanes,fmt='%s')

    if laneswithoutDwConn or laneswithoutDwConn or shadyLanes or nonExistentLanes:
        print "+++ Some connections are not right; Please check the Corrections folder before proceding"
        pdb.set_trace()

    connFilter = {}
    for conn in connAttributes:
        fLane,tLane = conn
        if fLane in laneSet and tLane in laneSet:
            connFilter[conn] = connAttributes[conn]

    pdb.set_trace()
    return connFilter




#==================================================================================================

def removeUTurns(connections):
    '''
        removing the connections representing U-turns at the intersections
            Yet To write
    '''
#=================================================================================================

def getNodeTypes(G):
    '''
    '''
    sourceNodes = [i for i in G if G.in_degree(i)==0]
    sinkNodes = [i for i in G if G.out_degree(i)==0]
    #---Getting the list of nodes that can be removed
    uniNodes = [] # The list of points that need not be modelled as a node.
    for node in G.nodes_iter():
        try:
            point = points[node]
            if point["trafficLid"]!='0':
                continue # traffic light is always a node
        except:
            pass
        outLinks = G.out_edges(node,data=True)
        inLinks = G.in_edges(node,data=True)
        # case of --->o--->
        if len(inLinks)==1 and len(outLinks)==1:
            uniNodes.append(node)
            continue
        # case of o===o===o
        if len(inLinks)==2 and len(outLinks)==2:
            ctpsIn = set([item[2]['ctpsid'] for item in inLinks])
            ctpsOut = set([item[2]['ctpsid'] for item in outLinks])
            if ctpsIn==ctpsOut:
               uniNodes.append(node)

    nodeDict = {'source':sourceNodes,'sink':sinkNodes,'uniNodes':uniNodes}  # A dictionary of source and sink nodes (not the final nodes in the network)

    return nodeDict
#==================================================================================================

def segmentToLink(baseAttributes):
    '''
        segmentToLink():
    '''

    G = nx.MultiDiGraph()
    for id,section in baseAttributes.iteritems():
        G.add_edge(section['FNODE'],section['TNODE'],id=id,ctpsid=section['ctps_ID'])

    nodeDict = getNodeTypes(G)
    sourceLinks =   [edge[2]['id'] for node in nodeDict['source'] for edge in G.out_edges(node,data=True)]

    segments = []           # Initiate list containing all segments of current link
    queue = []              # Maintain a list for setions to search
    visited = set()            # Maintain a list for sections searched
    linkCount = 1
    count_segments = 0
    linkToSeg = {}
    segToLink = {}
    stop = False

    #nx.dfs_edges(G, source='91139')
    #intoSections = list(set([conn['to_section'] for key,conn in connAttributes.iteritems()]))
    #intoSections = set(baseAttributes.keys()) - set([edge[2]['id'] for node in nodeDict['source'] for edge in G.out_edges(node,data=True)])
    for id,section in baseAttributes.iteritems():
        #if id not in visited and id in sourceLinks: # Search from all source sections: Running DFS to search the network
        #print "@ DFS; id: ", id
        if id not in visited:
            #visited.add(id)
            #print 'start searching from segment ' + repr(id)
            queue.append(id)
            while queue!=[]:
                segment_id = queue.pop()
                if segment_id in visited:
                    continue

                visited.add(segment_id)
                section = baseAttributes[segment_id]
                count_segments += 1
                tnode,hnode,curr_ctpsid = section['FNODE'],section['TNODE'],section['ctps_ID']
                #---Checking if the new segmet will form a cycle if associated with other segments in list
                cycle = hnode in [segment['FNODE'] for segment in segments]+[segment['TNODE'] for segment in segments]
                #---Checking if the new segment is not sequential to the other segments in the list
                notconnected = False
                if len(segments)>0:
                    notconnected = not tnode==segments[-1]['TNODE']
                #print "Segment id: ", segment_id, len(segments)
                #pdb.set_trace()
                # the link ends at the tnode of this section
                if (notconnected and len(segments)!=0) or cycle:
                    #print "Building Link with :" ,[seg['ID'] for seg in segments]
                    #pdb.set_trace()
                    linkToSeg[str(linkCount)] = [seg['ID'] for seg in segments] # creating a new link
                    for seg in segments:
                        segToLink[seg['ID']] = str(linkCount)
                    linkCount += 1
                    segments = [section]
                else:
                    if tnode in nodeDict['uniNodes']:
                        segments.append(section)
                        #print "segmentList :" ,[seg['ID'] for seg in segments]
                        #pdb.set_trace()

                    elif (len(G.in_edges(tnode))>1 and len(segments)!=0) or (len(G.out_edges(tnode))>1 and len(segments)!=0):
                        #print "Building Link with :" ,[seg['ID'] for seg in segments]
                        #pdb.set_trace()
                        linkToSeg[str(linkCount)] = [seg['ID'] for seg in segments] # creating a new link
                        for seg in segments:
                            segToLink[seg['ID']] = str(linkCount)
                        linkCount += 1
                        segments = [section]        # updating the segments list

                    else:
                        segments.append(section)
                #print "len of segList : ", len(segments)
                #pdb.set_trace()
                # Adding the outgoing edges to queue
                addLink = []
                out_edges = sorted(G.out_edges(hnode,data=True),key=lambda x: x[2]['id'])
                for edge in out_edges:
                    id,ctpsid = edge[2]['id'],edge[2]['ctpsid']
                    if id not in visited:
                        if ctpsid==curr_ctpsid:
                            addLink.insert(0,id)
                        else:
                            addLink.append(id)
                queue.extend(addLink)
                #print addLink
                #pdb.set_trace()
            #---dealing with the last segments
            if len(segments)!=0:
                linkToSeg[str(linkCount)] = [seg['ID'] for seg in segments] # creating a new link
                for seg in segments:
                    segToLink[seg['ID']] = str(linkCount)

    print "----Constructed the linkToSeg mapping: checking consistency ----",
    checkNetwork(linkToSeg,segToLink,baseAttributes)
    print "Done"
    pdb.set_trace()
    return segToLink,linkToSeg,nodeDict

#==================================================================================================

def constructSegmentsLinks(baseAttributes,basePoly,segToLink,linkToSeg,typeToWidthFname,ffsFname):
    '''
    '''
    ffsFunc = getHCMSpeeds(ffsFname) # reading the freeflow speed file
    linkcatToType = {}
    linkcatTocat = {}
    with open(typeToWidthFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            linkcatToType[row['LinkCat']] = row['Roadtype']
            linkcatTocat[row['LinkCat']] = row['CategoryID']

    #---contructing the Segment polylines (dealing with the uninodes and their removal from the data
    for link,segsInLink in linkToSeg.iteritems():
        #---checking if uninode exits
        if len(segsInLink)>1:
            for seg1,seg2 in itertools.izip(segsInLink,segsInLink[1:]):
                point1 = basePoly[seg1][-1]
                point2 = basePoly[seg2][0]
                newpoint = {'x':getAvg(point1['x'],point2['x']), 'y':getAvg(point1['y'],point2['y'])}
                # update basePoly
                newpoint1 = copy.deepcopy(newpoint)
                newpoint1.update({'ID':point1['ID'] , 'shapeid':point1['shapeid'] , 'seq': str(int(point1['seq'])+1)})
                basePoly[seg1].append(newpoint1)

                newpoint2 = copy.deepcopy(newpoint)
                newpoint2.update({'ID':point2['ID'] , 'shapeid':point2['shapeid'] , 'seq': str(0)})
                basePoly[seg2].insert(0,newpoint2)
                for i in xrange(len(basePoly[seg2])):
                    basePoly[seg2][i]['seq'] = str(i+1)


    segments = {}
    links = {}
    #----THE GBA DATA IS FAULTY!!!!!!!!!!!!!!!!!!!!!!!!!SOME VALUES ARE MISSING!!!!!!!!!!!!!!!!COMMENTING THOSE OUT!!!!!!!!!!!!!!!!!!!!!!
    #---Constructing segment objects
    for linkid,segsInLink in linkToSeg.iteritems():
        sequence = 1
        for segid in segsInLink:
            section = baseAttributes[segid]
            position = basePoly[segid]
            try:
                tag = "<old_id:"+str(section['OLD_ID'])+ ">," + "<link_cat:" + str(section['LinkCat']) + ">"
            except:
                tag = None
            #---the freeflow speeds are changed only if they are less than 40kmph (25mph)
            if float(section['SPEED']) < 40:
                maxspeed = getFfs(section['LinkCat'],int(section['NB_LANES']),float(section['CAPACITY']),ffsFunc)
            else:
                maxspeed = float(section['SPEED'])
            pointList = [(float(point['x']),float(point['y'])) for point in position]
            segLength = getLength(pointList)
            segment = Segment(segid,linkid,int(sequence),int(section['NB_LANES']),float(section['CAPACITY']),maxspeed,tag,linkcatTocat[section['LinkCat']],position,segLength)
            #segment = Segment(segid,linkid,int(sequence),int(section['NB_LANES']),None,float(section['SPEED']),tag,catToType[section['LINKCAT']],position)
            segments[segid] = segment
            sequence += 1

        #---Construction of link
        #linkCatMap = {'A':1,'B':2,'C':3,'D':4,'E':5,'SLIPROAD':6}
        tnode = baseAttributes[segsInLink[0]]['FNODE'] # tail node of first segment
        hnode = baseAttributes[segsInLink[-1]]['TNODE'] # head node of the last segment
        rname = baseAttributes[segsInLink[0]]['NAME']
        road_type = linkcatToType[baseAttributes[segsInLink[0]]['LinkCat']]
        linkcategory = linkcatTocat[baseAttributes[segsInLink[0]]['LinkCat']]
        link = Link(linkid,road_type,linkcategory,tnode,hnode,rname,segments = segsInLink)
        links[linkid] = link

    #---Contructing Link Travel Time Table
    linktts = {}
    for linkid,link in links.iteritems():
        linkTime,linkLength = 0,0
        for segid in link.segments:
            segLength = segments[segid].length
            segTime =  segLength/(segments[segid].speedlimit*(0.277778))
            linkLength += segLength
            linkTime += segTime
        #length = getLength(pointList)
        #traveltime = length/20.833    #75kmph in m/s
        linktts[linkid] = LinkTT(linkid,mode="Car",starttime="00:00:00",endtime="23:59:59",traveltime=linkTime,length=linkLength)


    return segments,links,linktts

#==================================================================================================

def constructNodes(links,points):
    '''
        constructNodes(): Constructs nodes from the head and tail node of the links
                          1. Gets the set of all nodes 2. Build node objects from points files
    '''
    #---Geting the list of all nodes' ids
    nodeidList = []
    for linkid,link in links.iteritems():
        nodeidList.extend([link.upnode,link.dnnode])

    nodeidList = list(set(nodeidList))

    #---Constructing nodes from points
    nodes = {}
    nodesShady = [] # Nodes without the pint information
    for id in nodeidList:
        try:
            point = points[id]
            node = Node(point['nodeid'],None,point['trafficLid'],point['x'],point['y'])
        except:
            node = Node(id,None,None,None,None)
            nodesShady.append(id)
        nodes[id] = node

    #---Writing the bad nodes into a file
    np.savetxt(os.path.join(errorFolder,'nodeWithoutPoints.txt'),nodesShady,fmt='%s')
    if nodesShady:
        print "+++ Some nodes do not have point information; Please check the Corrections folder before proceding"
        pdb.set_trace()
    return nodes

#===================================================================================================

def constructLanes(segments,typeToWidthFname):
    '''
    '''
    catToWidth = {}
    with open(typeToWidthFname,'rb') as ifile:
        reader = csv.DictReader(ifile)
        for row in reader:
            catToWidth[int(row['CategoryID'])] = row

    #---Contructing lanes attributes
    lanes = {}
    for segid,segment in segments.iteritems():
        for i in xrange(segment.numlanes):
            laneid = int(segid)*100 + i
            width = catToWidth[segment.category]['LaneWidth']
            lane = Lane(laneid,segid,width)
            lanes[str(laneid)] = lane

    #---Contructing lane polylines
    for segid,segment in segments.iteritems():
        segPos = segment.position
        segPos = [(float(item['x']),float(item['y'])) for item in segPos]
        #---looping over the lanes from the slowest to fastest
        for i in xrange(segment.numlanes):
            laneid = str(int(segid)*100 + i)
            width = float(catToWidth[segment.category]['LaneWidth'])
            if segment.numlanes==1:
                lanePos = segPos
            elif segment.numlanes==2:
                lanePos = offsetPolyLine(segPos,(-0.5+i)*width)
            elif segment.numlanes==3:
                lanePos = offsetPolyLine(segPos,(-1+i)*width)
            elif segment.numlanes==4:
                lanePos = offsetPolyLine(segPos,(-1.5+i)*width)
            elif segment.numlanes==5:
                lanePos = offsetPolyLine(segPos,(-2.+i)*width)
            elif segment.numlanes==6:
                lanePos = offsetPolyLine(segPos,(-2.5+i)*width)
            elif segment.numlanes==7:
                lanePos = offsetPolyLine(segPos,(-3.+i)*width)
            else:
                print "+++ @constructLanes(): The following case is not defined: numLanes: ", segment.numlanes
                pdb.set_trace()

            lanes[laneid].position = lanePos
    return lanes


#==================================================================================================

def constructConnections(connSumo,nodes,links,segments,lanes,segToLink):
    '''
        getConnections() : 1. Constructs the connections from the input connections
                           2. Contructs the polyline for the connections by drawing a straight line from the end of
                                    from 'section' to begining of to section
    '''
    connections = {}
    #---Constructing connections
    count = 1
    #----Constructing lane connections --- connections between segments of the same link
    for linkid,link in links.iteritems():
        for seg1,seg2 in zip(link.segments,link.segments[1:]):
            maxSpeed = min(segments[seg1].speedlimit,segments[seg2].speedlimit)
            for i in xrange(segments[seg1].numlanes):
                laneid1 = str(int(seg1)*100 + i)
                for j in xrange(segments[seg2].numlanes):
                    laneid2 = str(int(seg2)*100 + j)
                    connKey = (laneid1,laneid2)
                    connection = LaneConnection(count,laneid1,laneid2,seg1,seg2,isturn=False,maxspeed=maxSpeed,groupid=None)
                    connections[connKey] = connection
                    count += 1

    print "Number of lane connections: " , count

    connections,turninggroups,count = constructTurningPathsAll(nodes,links,segments,connections,lanes,count)
    # connections,turninggroups,count = constructTurningPathsSumo(connSumo,segToLink,nodes,links,segments,connections,lanes,count)


    print "Number of lane connections + turning paths: ", count

    return connections,turninggroups


#===================================================================================================

def constructTurningPathsSumo(connSumo,segToLink,nodes,links,segments,connections,lanes,conncount):
    '''
    '''
    turningdict = {}
    turninggroups = {}
    groupcount = 1
    for key,conn in connSumo.iteritems():
        fromLane, toLane = conn['from_lane'],conn['to_lane']
        connKey = (fromLane,toLane)
        #---Constructing the connections
        #pdb.set_trace()
        if connKey not in connections:
            node = conn['nodeid']
            fromSec,toSec = conn["from_section"],conn["to_section"]
            fromLink,toLink = segToLink[fromSec], segToLink[toSec]
            #---Checking if the connection is a turning
            sameNode = (links[fromLink].dnnode==links[toLink].upnode) and (links[fromLink].dnnode==node) #checking if the connection is through the same node
            #print "node in Nodes: ", node in nodes
            #print "Same node: ", sameNode
            #pdb.set_trace()
            if node in nodes and sameNode:
                #print "@ln: 423"
                #pdb.set_trace()
                if fromSec in segments and toSec in segments:
                    isSequential = (segments[fromSec].seq==len(links[fromLink].segments)) and segments[toSec].seq==1
                    # checking that segments are sequential
                    if isSequential:
                        if (fromLink,toLink) not in turningdict:
                            turningdict[(fromLink,toLink)] = {'id':groupcount}
                            turninggroup = TurningGroup(groupcount,node,fromLink,toLink)
                            turninggroups[(fromLink,toLink)] = turninggroup
                            groupcount +=1
                        maxSpeed = min(segments[fromSec].speedlimit,segments[toSec].speedlimit)
                        groupid = turninggroups[(fromLink,toLink)].id
                        connection = LaneConnection(conncount,fromLane,toLane,fromSec,toSec,isturn=True,maxspeed=maxSpeed,groupid=groupid)
                        #---Constructing the connection polyline
                        firstpoint = lanes[fromLane].position[-1]
                        secondpoint = lanes[toLane].position[0]
                        connection.position = [firstpoint,secondpoint]
                        connections[connKey] = connection
                        conncount += 1
    return connections,turninggroups,conncount

#====================================================================================================

def offsetPolyLine(polyLine,offset):
    '''
    '''

    if len(polyLine)==1:
        print "+++ @offsetPolyLine(): polyline has only 1 point"
        pdb.set_trace()

    if abs(offset)<10**-6:
        return polyLine
    lineList = []
    # off-set all the lines (pairs of points)
    for point1,point2 in zip(polyLine,polyLine[1:]):
        dx = point2[0]-point1[0]
        dy = point2[1]-point1[1]
        try:
            n = np.array([-dy,dx])/norm([-dy,dx])
        except e:
            pdb.set_trace()
        if not type(norm([-dy,dx])) is np.float64:
            pdb.set_trace()

        offpoint1 = np.array(point1) + offset*n
        offpoint2 = np.array(point2) + offset*n
        lineList.append([offpoint1,offpoint2])

    #print lineList
    offsetPolyLine = []
    #---determing the middle points of two offset line
    if len(polyLine)>2:
        for line1,line2 in zip(lineList,lineList[1:]):
            m1 = (line1[1][1]-line1[0][1])/(line1[1][0]-line1[0][0])
            c1 = line1[1][1] - m1*line1[1][0]
            m2 = (line2[1][1]-line2[0][1])/(line2[1][0]-line2[0][0])
            c2 = line2[1][1] - m2*line2[1][0]
#            if (line1[1][0]-line1[0][0])==0:
#                pdb.set_trace()
            interx = (c2-c1)/(m1-m2)
            intery = m1*interx + c1
            offsetPolyLine.append(np.array([interx,intery]))

    #---inserting the first and last points
    offsetPolyLine.insert(0,lineList[0][0])
    offsetPolyLine.append(lineList[-1][1])

    #---Should be updated to handle exceptions where inf is at the end points
    for i in xrange(len(offsetPolyLine)):
        point = offsetPolyLine[i]
        if point[0]==np.inf or point[1]==np.inf:
            p1,p2 = offsetPolyLine[i-1],offsetPolyLine[i+1]
            newp = (p1+p2)/2.
            offsetPolyLine[i] = newp

    return offsetPolyLine

#==================================================================================================


def checkNetwork(linkToSeg,segToLink,baseAttributes):
    '''
    '''
    #---Checking if the segments in a given link are sequential
    for link,segsInLink in linkToSeg.iteritems():
        aList = []
        for seg in segsInLink:
            aList.extend([baseAttributes[seg]['FNODE'],baseAttributes[seg]['TNODE']])
        aList = aList[1:-1]
        error = False
        for i in xrange(0,len(aList),2):
            if aList[i] != aList[i+1]:
                error=True
        if error:
            print "+++ @checkNetwork: : The following link has non sequential segments: ", link
            pdb.set_trace()

    #--Checking if all segments have been associated to a link and no segment is associated with more than one link
    numSections = len(baseAttributes)
    numSegs = 0
    segList = set()
    for link,segsInLink in linkToSeg.iteritems():
        numSegs += len(segsInLink)
        if not segList.isdisjoint(set(segsInLink)):
            print "+++ @checkNetwork: : A segment is associated with multiple links: ", segsInLink
            pdb.set_trace()
        else:
            segList.update(segsInLink)

    if numSections!=numSegs:
        print "+++ @checkNetwork: : There are segments without link associations:"
        pdb.set_trace()


#===================================================================================================

def getAvg(a1,a2):
    if type(a1) is str or type(a2) is str:
        return (float(a1)+float(a2))/2.
    else:
        return (a1+a2)/2.

def getLength(pList):
    length = 0
    for p1,p2 in zip(pList,pList[1:]):
        length += math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    return length
