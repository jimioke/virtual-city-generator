# Prepare network edges and vertexes

#---load functions
source("~/Desktop/public-transit-graph/correct-full-generation/R files/SimM_Access_Egress_legs.R")
source("~/Desktop/public-transit-graph/correct-full-generation/R files/SimM_stopsTOwalk_legs.R")
source("~/Desktop/public-transit-graph/correct-full-generation/R files/Generate_SimM_Route_Segment.R")

# -----------------------generate BUS  route segment from raw data
#INPUT1: use updated schedule and stop files from SimMobility
bus_routes<-fread(bus_routes_dir, header = TRUE)
  {
#---input bus_routes, generate bus route segments.
# input format: 
#---------:#service_id trip_id stop_id stop_sequence arrival_time departure_time dwelling_time
# output format:
# -----------start_stops end_stops r_type service_id Road_Index stop_link_sequence road_edge_id r_service_lines link_travel_time edge_id
#-------1:       10009     10089    Bus      131_2          1                  1            1   131_2/167_2/275_1/5_2               45       1

links<-Generate_SimM_Route_Segment(bus_routes, "Bus")

#-------waiting time. 
#!!!!! Need to update this part when SimMobility is able to give frequency data
#------current assumption is uniform headway 10min per line
links[,wait_time:=300.0/(str_detect(r_service_lines, "/")+1)]

#---dummy walk_time to avoid generate unreasonable path during choice set generation
#---not used for path attributes computation
links[, walk_time:=10.0]
links[,transit_time:=link_travel_time]
#-----transfer penalty used for choice set generation only
links[, transfer_penalty:=2*wait_time]

#------------need to update his part for night_transit_time and wait_time when SimMobility has correct night buses and frequencies
links[, day_transit_time:=transit_time]
links[str_detect(r_service_lines, "/")==1L & str_detect(r_service_lines, "N")>=1, day_transit_time:=2000.0]

#---update this portion when simMobility provides travel distance
links[,dist:=link_travel_time/3600*35]

links<-links[!is.na(day_transit_time)]
}
#OUTPUT1: bus route segments file
write.csv(links, file = Bus_routes_seg_dir, row.names=FALSE)

#INPUT2: --bus stops files
Sim_busStops<-fread(Bus_stops_dir, header = TRUE)
  {
#---------------------get txf between bus_stops---------------
RTS_radius<-1.5
Bus_radius<-0.8
links<-SimM_stopsTOwalk_legs(Sim_busStops,Sim_busStops, RTS_radius, Bus_radius)

#  dummy wait time create for walking links. Can assist choice set generation. 
#  should not used for path attributes generation
links[,wait_time:=10.0]
links[, walk_time:=link_travel_time]
links[, transit_time:=0.0]
# can adjust for better choice set generation
links[, transfer_penalty:=2*walk_time]
links[, day_transit_time:=transit_time]
# assumed walking speed is 4km/hour
links[, dist:=link_travel_time/3600*4]

}
#OUTPUT2: ---output walk tranfer files between buses
write.csv(links, file = Bus_txfWalk_dir, row.names=FALSE)

# INPUT3: origin and destination nodes file
P_nodes<-fread(local_P_nodes_dir, header=TRUE)
#---change column to make sure P_nodes, Bus_stops, train_stops are the same
P_nodes[, stopType:=NULL]
P_nodes[, Type:=0]
P_nodes[, stopType:=0]
{
# assumed maximum 5 stations for RTS and 30 stops for Bus-stops.
#  Could adjust during choice set generation
RTS_N<-5
Bus_N<-30

links<-SimM_AccEgr_legs(P_nodes, Sim_busStops, RTS_N, Bus_N)

# wait time is dummy variables used to assist choice set generation. Could ignore.Could change to 0
# should not used for path attribute computation
links[, wait_time:=10.0]
links[, walk_time:=link_travel_time]
links[, transit_time:=0.0]
links[, transfer_penalty:=2000.0]
links[, day_transit_time:=transit_time]
# dist compuation:::::4km/hour walking speed. 
#Should be updated when SimMobility has pedestrain network
links[, dist:=link_travel_time/3600*4]

}

#OUTPUT3: access egress links to Bus stops
write.csv(links, file = AccEgr_Bus_dir, row.names=FALSE)


## -----------------------generate MRT  route segment from raw data
# It is currently using Google Transit Data
# need to update this part as BUS when SimMobility creates its MRT/LRT network
# Google Transit data is update to follow SimMobility format



# INPUT4 ----RTS schedule sequence
train_routes<-fread(RTS_routes_dir, header = TRUE)

{
links<-Generate_SimM_Route_Segment(train_routes, "RTS")
# assumped 4 minutes headway. Should update his part with SimMobility frequencies
links[, wait_time:=120.0]
# account for walk from station to platform
links[, walk_time:=50.0]
links[,transit_time:=link_travel_time]
# could ajust for better choice set generation
links[, transfer_penalty:=2*wait_time]
links[, day_transit_time:=transit_time]
# assumed 75km/hour speed. Should update when SimMobility provide distance
links[,dist:=link_travel_time/3600*75]
}
#OUTPUT 4 ------ RTS route segment files
write.csv(links, file = RTS_routes_seg_dir, row.names=FALSE)


#INPUT 5------generate RTS transfers----RTS stops
train_stops<-fread(RTS_stops_dir, header = TRUE)
#----RTS_txf
{
  RTS_radius<-1.5
  Bus_radius<-0.8
  links<-SimM_stopsTOwalk_legs(train_stops, train_stops, RTS_radius, Bus_radius)
 #dummy variable. could change to zero. Assist choice set generaiton.
  # should not use for path attribute computation
  links[, wait_time:=10.0]
  links[, walk_time:=link_travel_time]
  links[, transit_time:=0.0]
  links[, transfer_penalty:=2*walk_time]
  links[, day_transit_time:=transit_time]
  # assumed 4km/hour walking speed. Should update when SimMobility has detailed transfer geometry information
  links[, dist:=link_travel_time/3600*4]

}
#OUTPUT 5 --- walk transfers among RTS 
write.csv(links, file = RTS_txfWalk_dir, row.names=FALSE)

#INPUT6--Generate access and egress to RTS -AccEgr_RTS
{
  RTS_N<-5
  Bus_N<-30
  links<-SimM_AccEgr_legs(P_nodes, train_stops, RTS_N, Bus_N)
  #dummy could update to 0. not used for path attribute computaiton
  links[, wait_time:=10.0]
  # All walk_time is based on direct distance and assumed 4km/hour speed. should update when SimMobility provide exact information
  links[, walk_time:=link_travel_time]
  links[, transit_time:=0.0]
  # large penalty to assist choice set generation. Not used for path attributes
  links[, transfer_penalty:=2000.0]
  links[, day_transit_time:=transit_time]
  # assumed 4km/hour speed. should update when SimMobility provide exact information
  links[, dist:=link_travel_time/3600*4]

}
#OUTPUT6---- access and egress to RTS
write.csv(links, file = AccEgr_RTS_dir, row.names=FALSE)


#INPUT7----Generate transfer between Bus & RTS--bus_stops, train_stops
{
#----RTS_Bus_Txf
RTS_Bus_txfWalk<-SimM_stopsTOwalk_legs(Sim_busStops, train_stops, RTS_radius, Bus_radius)
Bus_RTS_txfWalk<-SimM_stopsTOwalk_legs(train_stops,Sim_busStops,  RTS_radius, Bus_radius)
links<-rbind(RTS_Bus_txfWalk, Bus_RTS_txfWalk)

#dummy could update to 0. not used for path attribute computaiton
links[, wait_time:=10.0]
# All walk_time is based on direct distance and assumed 4km/hour speed. should update when SimMobility provide exact information
links[, walk_time:=link_travel_time]
links[, transit_time:=0.0]
links[, transfer_penalty:=2*walk_time]
links[, day_transit_time:=transit_time]
# assumed 4km/hour speed. should update when SimMobility provide exact information
links[, dist:=link_travel_time/3600*4]
}
#OUTPUT7 -----transfer between Bus & RTS
write.csv(links, file = RTS_Bus_txfWalk_dir, row.names=FALSE)







