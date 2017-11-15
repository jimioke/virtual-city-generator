import networkx as nx
import numpy as np
import csv,pdb,os,itertools,copy
from collections import OrderedDict
from numpy.linalg import norm
from network import *


def processAndAddConnections(nodes,tempnodeDict,links,segments,lanes,laneconnections,turninggroups,segToLink):
    '''
    '''
    laneswithDwConn = []  # lanes with downstream connections
    laneswithUpConn = []  # lanes with upstream connections

    for connid,conn in laneconnections.iteritems():
        fLane,tLane = conn.fromlane,conn.tolane
        laneswithDwConn.append(fLane)
        laneswithUpConn.append(tLane)
    laneswithDwConn,laneswithUpConn = set(laneswithDwConn),set(laneswithUpConn)

    totLaneList = lanes.keys()
    terlaneswithoutDwConn, terlaneswithoutUpConn = set(),set()

    #---Getting the terminal lanes ---lanes at the end and begining of links--- that are not connected to sink (source) node and no downstream (upstream) connection
    for linkid,link in links.iteritems():
        tnode,hnode = link.upnode,link.dnnode
        #---first segment
        segid = link.segments[0]
        segment = segments[segid]
        for i in xrange(segment.numlanes):
            laneid = str(int(segid)*100 + i)
            if laneid not in laneswithUpConn and tnode not in tempnodeDict['source']:
                terlaneswithoutUpConn.add(laneid)
        #---last segment
        segid = link.segments[-1]
        segment = segments[segid]
        for i in xrange(segment.numlanes):
            laneid = str(int(segid)*100 + i)
            if laneid not in laneswithDwConn and hnode not in tempnodeDict['sink']:
                terlaneswithoutDwConn.add(laneid)


    #----Handling lanes without downstream connections
    unresolvedLanes = []
    connKeylist = laneconnections.keys()
    count = len(connKeylist) + 1 # count and id of the connections
    #---Copying the connections from one of the adjacent lanes
    for laneid1 in terlaneswithoutDwConn:
        resolved = False
        segid1 = laneid1[:-2]
        segid1 = int(segid1)
        for i in xrange(segments[segid1].numlanes):
            laneid2 = str(int(segid1)*100 + i)
            if laneid1!=laneid2:
                connkeys = [key for key in connKeylist if key[0]==laneid2]
                if connkeys:
                    fromLane,toLane = connkeys[0]
                    tosegid = toLane[:-2]
                    linkid1,toLink = segToLink[segid1],segToLink[tosegid]
                    maxSpeed = min(segments[segid1].speedlimit,segments[tosegid].speedlimit)
                    groupid = turninggroups[(linkid1,toLink)].id
                    connection = LaneConnection(count,laneid1,toLane,segid1,tosegid,isturn=True,maxspeed=maxSpeed,groupid=groupid)
                    #---Constructing the connection polyline
                    firstpoint,secondpoint = lanes[laneid1].position[-1],lanes[toLane].position[0]
                    connection.position = [firstpoint,secondpoint]
                    laneconnections[(laneid1,toLane)] = connection
                    count += 1
                    resolved = True
                    break
        if not resolved:
            unresolvedLanes.append(laneid1)
            # pdb.set_trace()

    print "Before: ",len(terlaneswithoutDwConn)
    print "After: ",len(unresolvedLanes), unresolvedLanes
    #laneswithoutDwConn = set(totLaneList) - laneswithDwConn
    #laneswithoutUpConn = set(totLaneList) - laneswithUpConn

    #-----Connecting to a lane from the list of downstream links
    #for laneid1 in unresolvedLanes:
        #resolved = False
        #segid1 = laneid1[:-2]
        #linkid1 = segments[segid].linkid
        #node = links[linkid1].dnnode
        #potLinks = {k:v for k,v in links.iteritems() if v.upnode==node} # list of linkids with node as upnode: potential connections
        #linksegList = [(linkid,link.segments[0]) for linkid,link in potLinks.iteritems()] # list of first segments in the potential links
        #for linkid2,segid2 in linksegList:
            #if resolved: break
            #if (linkid1,linkid2) not in turninggroups:
                #groupcount = len(turninggroups)
                #turninggroup = TurningGroup(groupcount,node,linkid1,linkd2)
                #turninggroups[(linkid1,linkid2)] = turninggroup
                #print "@processAndAddConnections(): created new turninggroup"
            #if (linkid1,linkid2) in turninggroups:
                #groupid = turninggroups[(linkid1,linkid2)].id
            #else:
                #print "groupid does not exist.."
                #pdb.set_trace()
            #for i in xrange(segments[segid2].numlanes):
                #laneid2 = str(int(segid2)*100 + i)
                #maxSpeed = min(segments[segid1].speedlimit,segments[segid2].speedlimit)
                #connection = LaneConnection(count,laneid1,laneid2,segid1,segid2,isturn=True,maxspeed=maxSpeed,groupid=groupid)
                ##---Constructing the connection polyline
                #firstpoint,secondpoint = lanes[laneid1].position[-1],lanes[laneid2].position[0]
                #connection.position = [firstpoint,secondpoint]
                #laneconnections[(laneid1,laneid2)] = connection
                #count+=1
                #resolved = True




    # pdb.set_trace()
    return laneconnections

#===================================================================================================

def constructTurningPathsAll(nodes,links,segments,connections,lanes,conncount):
    '''
        Constructs turning paths such that every link is connected to all its downstream links.
        Specifically, all the lanes in the last segment of a link are connected to all the lanes in the first segment of
        every downstream link
    '''

    #---Construct MultiDiGraph
    netG = nx.MultiDiGraph()
    for link_id,link in links.iteritems():
        netG.add_edge(link.upnode,link.dnnode,id=link_id)


    turningdict = {}
    turninggroups = {}
    groupcount = 1
    #---Looping over ajdacent links and then contructing connections between their lanes
    for edge1 in netG.edges(data=True):
        hnode,fromLink = edge1[1],edge1[2]['id']
        fromSeg = links[fromLink].segments[-1]
        #pdb.set_trace()
        assert segments[fromSeg].seq == len(links[fromLink].segments) #making sure that it is the last segment
        for i1 in xrange(segments[fromSeg].numlanes):
            fromLane = str(int(fromSeg)*100 + i1)
            for edge2 in netG.out_edges(hnode,data=True):
                toLink = edge2[2]['id']
                if (fromLink,toLink) not in turningdict:
                    turningdict[(fromLink,toLink)] = {'id':groupcount}
                    turninggroup = TurningGroup(groupcount,hnode,fromLink,toLink)
                    turninggroups[(fromLink,toLink)] = turninggroup
                    groupcount +=1

                toSeg = links[toLink].segments[0]
                assert segments[toSeg].seq == 1 #making sure that it is the first segment
                #pdb.set_trace()
                for i2 in xrange(segments[toSeg].numlanes):
                    toLane = str(int(toSeg)*100 + i2)
                    maxSpeed = min(segments[fromSeg].speedlimit,segments[toSeg].speedlimit)
                    groupid = turninggroups[(fromLink,toLink)].id
                    connection = LaneConnection(conncount,fromLane,toLane,fromSeg,toSeg,isturn=True,maxspeed=maxSpeed,groupid=groupid)
                    #---Constructing the connection polyline
                    firstpoint = lanes[fromLane].position[-1]
                    secondpoint = lanes[toLane].position[0]
                    connection.position = [firstpoint,secondpoint]
                    connections[(fromLane,toLane)] = connection
                    conncount += 1

    return connections,turninggroups,conncount
