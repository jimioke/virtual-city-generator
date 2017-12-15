import os,csv,pdb
from operator import itemgetter

class Network:
    
    def __init__(self,nodes,links,segments,lanes,laneconnections,turninggroups,linktts):
        self.nodes = nodes
        self.links = links
        self.segments = segments # constructed at the final stage
        self.lanes = lanes
        self.laneconnections = laneconnections
        self.turninggroups = turninggroups
        self.linktts = linktts
        self.numNodes = len(self.nodes)
        self.numLinks = len(self.links)
        self.numSegs = len(self.segments)
    
    def write(self,foldername):
        #---Writing nodes
        nodeFname = os.path.join(foldername,'node-nodes.csv')
        with open(nodeFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(['id','x','y','z','traffic_light_id','tags','node_type'])
            nodeList = self.nodes.keys()
            nodeList = sorted([int(item) for item in nodeList])
            for id in nodeList:
                node = self.nodes[str(id)]
                writer.writerow(node.render())

        #---Writing segments
        segFname1 = os.path.join(foldername,'segment-attributes.csv')
        segFname2 = os.path.join(foldername,'segment-nodes.csv')
        with open(segFname1,'wb') as ofile1:
            with open(segFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                segList = self.segments.keys()
                segList = sorted([int(item) for item in segList])
                for id in segList:
                    segment = self.segments[str(id)]
                    writer1.writerow(segment.render())
                    for point in segment.position:
                        aList = [id,point['x'],point['y'],0,point['seq']]
                        writer2.writerow(aList)

        #---Writing segments
        segFname1 = os.path.join(foldername,'segment-attributes_more.csv')
        with open(segFname1,'wb') as ofile1:
            writer1 = csv.writer(ofile1)
            writer1.writerow(['id','link_id','sequence','num_lanes','capacity','max_speed','tags','link_category','length'])
            segList = self.segments.keys()
            segList = sorted([int(item) for item in segList])
            for id in segList:
                segment = self.segments[str(id)]
                writer1.writerow(segment.render2())


        
        #---Writing links
        linkFname1 = os.path.join(foldername,'link-attributes.csv')
        linkFname2 = os.path.join(foldername,'link-nodes.csv')
        with open(linkFname1,'wb') as ofile1:
            with open(linkFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','road_type','category','from_node','to_node','road_name','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                linkList = self.links.keys()
                linkList = sorted([int(item) for item in linkList])
                for id in linkList:
                    link = self.links[str(id)]
                    writer1.writerow(link.render())
                    count = 1
                    for segid in link.segments:
                        for point in self.segments[segid].position:
                            aList = [id,point['x'],point['y'],0,count]
                            writer2.writerow(aList)
                            count += 1

        #---Writing lanes
        laneFname1 = os.path.join(foldername,'lane-attributes.csv')
        laneFname2 = os.path.join(foldername,'lane-nodes.csv')
        with open(laneFname1,'wb') as ofile1:
            with open(laneFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','width','vehicle_mode','bus_lane','can_stop','can_park','high_occ_veh','has_road_shoulder','segment','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])                            
                laneList = self.lanes.keys()
                laneList = sorted([int(item) for item in laneList])
                for id in laneList:
                    lane = self.lanes[str(id)]
                    writer1.writerow(lane.render())
                    count = 1
                    for point in lane.position:
                        aList = [id,point[0],point[1],0,count]
                        writer2.writerow(aList)
                        count += 1

        #---Writing connections
        #---lane connections first (not turnings)
        connFname = os.path.join(foldername,'connector.csv')
        with open(connFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","from_segment","to_segment","from_lane","to_lane","is_true_connector","tags"])
            connList = [k for k,v in self.laneconnections.iteritems() if not v.isturn]
            connList = sorted([item for item in connList],key=itemgetter(0))        
            for id in connList:
                conn = self.laneconnections[id]
                writer.writerow(conn.render())                    

        #---Writing turning connections
        turnFname1 = os.path.join(foldername,'turning-attributes.csv')
        turnFname2 = os.path.join(foldername,'turning-nodes.csv')
        with open(turnFname1,'wb') as ofile1:
            with open(turnFname2,'wb') as ofile2:
                writer1 = csv.writer(ofile1)
                writer1.writerow(['id','from_lane','to_lane','group_id','max_speed','tags'])
                writer2 = csv.writer(ofile2)
                writer2.writerow(['id','x','y','z','seq_id'])
                turnList = [k for k,v in self.laneconnections.iteritems() if v.isturn]
                turnList = sorted([item for item in turnList],key=itemgetter(0)) 
                for id in turnList:
                    turn = self.laneconnections[id]
                    writer1.writerow(turn.render())
                    count = 1
                    for point in turn.position:
                        aList = [turn.id,point[0],point[1],0,count]
                        writer2.writerow(aList)
                        count += 1                    

        #---Writing turninggroups
        tgFname = os.path.join(foldername,'turninggroups.csv')
        with open(tgFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","nodeid","from_link","to_link","phases","rules","visibility","tags"])
            tgList = [k for k in self.turninggroups]
            tgList = sorted([item for item in tgList],key=itemgetter(0))        
            for id in tgList:
                tg = self.turninggroups[id]
                writer.writerow(tg.render())  

        #---Writing default link TTs
        ttFname = os.path.join(foldername,'linkttsdefault.csv')
        with open(ttFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","mode","starttime","endtime","traveltime"])
            linkList = self.linktts.keys()
            linkList = sorted([int(item) for item in linkList])        
            for id in linkList:
                linktt = self.linktts[str(id)]
                writer.writerow(linktt.render())                  

        #---Writing default link TTs
        ttFname = os.path.join(foldername,'linkttsdefault_more.csv')
        with open(ttFname,'wb') as ofile:
            writer = csv.writer(ofile)
            writer.writerow(["id","mode","starttime","endtime","traveltime","length"])
            linkList = self.linktts.keys()
            linkList = sorted([int(item) for item in linkList])        
            for id in linkList:
                linktt = self.linktts[str(id)]
                writer.writerow(linktt.render2())  

                
class Node:
    def __init__(self,id,type,tLightId,x,y,z=0):
        self.id = id
        self.type = type
        self.trafficLightId = tLightId
        self.x = x
        self.y = y
        self.z = z
        self.tag = None
        
    def render(self):
        aList = [self.id,self.x,self.y,self.z,self.trafficLightId,self.tag,self.type]
        return aList


class Link:
    
    def __init__(self,id,roadtype,category,upnode,dnnode,name,segments = None):
        self.id = id
        self.type = roadtype
        self.category = category
        self.upnode = upnode
        self.dnnode = dnnode
        self.name = name
        self.segments = segments
        self.tags = None
    
    def render(self):
        aList = [self.id,self.type,self.category,self.upnode,self.dnnode,self.name,self.tags]
        return aList

class LinkTT:
    
    def __init__(self,id,mode,starttime,endtime,traveltime,length):
        self.id = id
        self.mode = mode
        self.starttime = starttime
        self.endtime = endtime
        self.traveltime = traveltime
        self.length = length
        
    def render(self):
        aList = [self.id,self.mode,self.starttime,self.endtime,self.traveltime]
        return aList

    def render2(self):
        aList = [self.id,self.mode,self.starttime,self.endtime,self.traveltime,self.length]
        return aList

class Segment:
	
    def __init__(self,id,linkid,sequence,numlanes,capacity,speedlimit,tag,category,position,length):
        self.id = id
        self.linkid = linkid
        self.seq = sequence
        self.numlanes = numlanes
        self.capacity = capacity
        self.speedlimit = speedlimit
        self.category = category
        self.tag = tag
        self.position = position
        self.length = length
    
    def render(self):
        aList = [self.id,self.linkid,self.seq,self.numlanes,int(self.capacity),int(self.speedlimit),self.tag,self.category]
        #aList = ",".join(aList)
        return aList

    def render2(self):
        aList = [self.id,self.linkid,self.seq,self.numlanes,int(self.capacity),int(self.speedlimit),self.tag,self.category,self.length]
        #aList = ",".join(aList)
        return aList
   

class Lane:
    
    def __init__(self,id,segid,width,vehiclemode=None,buslane=0,canstop=0,canpark=0,hov=0,hasshoulder=0,position=None):
        self.id = id
        self.segid = segid
        self.width = width
        self.canstop = canstop
        self.canpark = canpark
        self.hov = hov
        self.hasshoulder = hasshoulder
        self.buslane = buslane
        self.vehiclemode = vehiclemode
        self.tags = None
        self.position = position
        
        
    def render(self):
        aList = [self.id,self.width,self.vehiclemode,self.buslane,self.canstop,self.canpark,self.hov,self.hasshoulder,self.segid,self.tags]
        return aList

class LaneConnection:
    def __init__(self,id,fromlane,tolane,fromsegment,tosegment,isturn,maxspeed,groupid):
        self.id = id
        self.fromlane = fromlane
        self.tolane = tolane
        self.fromsegment = fromsegment
        self.tosegment = tosegment
        self.isturn = isturn
        self.istrueconn = None
        self.maxspeed = maxspeed
        self.groupid = groupid       
        self.tags = None

    def render(self):
        if self.isturn:
            aList = [self.id,self.fromlane,self.tolane,self.groupid,int(self.maxspeed),self.tags]
        else:
            aList = [self.id,self.fromsegment,self.tosegment,self.fromlane,self.tolane,self.istrueconn,self.tags]
        return aList


class TurningGroup:
    
    def __init__(self,id,nodeid,fromlink,tolink):
        self.id = id
        self.nodeid = nodeid
        self.fromlink = fromlink
        self.tolink = tolink
        self.phases = None
        self.rules = None
        self.visibility = None
        self.tags = None
        
        
    def render(self):
        aList = [self.id,self.nodeid,self.fromlink,self.tolink,self.phases,self.rules,self.visibility,self.tags]
        return aList




class Sensor:
	def __init__(self,id,segmentId):
		self.id = id
		self.segmentId = segmentId

	def render(self):
		return "{256 0x0001 6 %d 0.5\n\t{%d 1}\n\t}\n" % (self.segmentId,self.id)