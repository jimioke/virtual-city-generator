#----------------------------update version number here for different back of data

# read in generated files
Bus_routes_seg<-fread(Bus_routes_seg_dir, header = TRUE)
Bus_txfWalk<-fread(Bus_txfWalk_dir, header = TRUE)
AccEgr_Bus<-fread(AccEgr_Bus_dir, header = TRUE)
RTS_routes_seg<-fread(RTS_routes_seg_dir, header = TRUE)
RTS_txfWalk<-fread(RTS_txfWalk_dir, header = TRUE)
AccEgr_RTS<-fread(AccEgr_RTS_dir, header = TRUE)
RTS_Bus_txfWalk<-fread(RTS_Bus_txfWalk_dir, header = TRUE)

#-------------generate walking links from P_nodes to PT stops-------------

network_types<-c("bus only", "bus+MRT")
for(t in 1:length(network_types))
{
  if(t==1)
  {
    stops<-rbind(P_nodes, Sim_busStops)
    links<-rbind(Bus_routes_seg,Bus_txfWalk, AccEgr_Bus)
    links<-links[!is.na(start_stops)]
    links<-links[!is.na(end_stops)] 
    links<-links[start_stops %in% stops$stop_id]
    links<-links[end_stops %in% stops$stop_id]
    links[, edge_id:=1:nrow(links)]
    stop_store_dir<-All_bus_stops_dir
    link_store_dir<-All_bus_links_dir
  }
  if(t==2)
  {
    stops<-rbind(P_nodes,Sim_busStops, train_stops)
    links<-rbind(Bus_routes_seg,Bus_txfWalk, AccEgr_Bus
                 ,RTS_routes_seg,RTS_txfWalk,AccEgr_RTS
                 ,RTS_Bus_txfWalk)
    links<-links[!is.na(start_stops)]
    links<-links[!is.na(end_stops)] 
    links<-links[start_stops %in% stops$stop_id]
    links<-links[end_stops %in% stops$stop_id]
    stop_store_dir<-All_PT_stops_dir
    link_store_dir<-All_PT_links_dir
    links[, edge_id:=1:nrow(links)]
  }
  #define search max distance
    write.csv(stops, stop_store_dir, row.names=FALSE)
    write.csv(links, link_store_dir, row.names=FALSE)
}


#----------codes to verify shortest paths and network 

{
# links<-fread(All_PT_links_dir, header=TRUE)
# stops<-fread(All_PT_stops_dir, header=TRUE)
# 
# #create graph
# g<-graph.data.frame(links, directed = TRUE, vertices = stops)
# 
# origin<-"N_461902"
# dest<-"N_94039"
# 
# #origin<-"N_11708"
# #dest<-"N_19405"
# #origin<-"N_10873"
# #dest<-"N_19973"
# #origin<-"N_1380034700"
# #dest<-"N_12244"
# 
# #search for shortest new_path
# new_path<- get.shortest.paths(g, origin, to = dest, 
#                               weights = E(g)$transit_time+E(g)$wait_time
#                               +2*E(g)$walk_time 
#                               +E(g)$transfer_penalty
#                               , output= "epath")$epath
}

