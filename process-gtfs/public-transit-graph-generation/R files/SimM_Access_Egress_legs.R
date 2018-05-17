# need PT_stops as global files

SimM_AccEgr_legs<-function(P_nodes, PT_stops, RTS_N, Bus_N)
{
  #  input formate
  #  stop_id stop_code stop_name stop_lat stop_lon EZLink_Name stopType
  #1: N_10001   N_10001   N_10001 1.310611 103.8728     N_10001        0
  

 # for each node, generate walk links from this nodes to all other nodes
  # filter out legs with dist>RTS_radius for RTS stops
  # filter out legs with dist>Bus_radius for Bus stops
  
  # for access
  setkeyv(P_nodes, NULL)
  setkeyv(PT_stops, NULL)
  mapped_stops<-setkey(P_nodes[,c(k=1,.SD)],k)[PT_stops[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]
  mapped_stops<-mapped_stops[abs(stop_lon-i.stop_lon)<0.1 & abs(stop_lat-i.stop_lat)<0.1]

  mapped_stops[, dist:=geodDist(stop_lon, stop_lat,i.stop_lon,i.stop_lat)]
  setkeyv(mapped_stops, "stop_id")
  mapped_stops<-mapped_stops[order(stop_id, dist)]
  mapped_stops[, Rank:=1:.N, by="stop_id"]
  # mapped_stops[, dist:=geodDist(OrigLon, OrigLat,OrigLon,stop_lat) + geodDist(OrigLon, OrigLat,stop_lon,OrigLat)]

  access_legs<-mapped_stops[Rank<=2L |(i.stopType==1L & Rank<=Bus_N & dist<=1.0) | (i.stopType==2L & Rank<=RTS_N & dist<=2.0)]
 
   setnames(access_legs, "stop_id", "start_stops")
   setnames(access_legs, "i.stop_id", "end_stops")
   setnames(access_legs, "stop_lat", "start_lat")
   setnames(access_legs, "stop_lon", "start_lon")
   setnames(access_legs, "i.stop_lat", "end_lat")
   setnames(access_legs, "i.stop_lon", "end_lon")
 
  egress_legs<-mapped_stops[Rank<=2L |(i.stopType==1L & Rank<=Bus_N & dist<=1.0) | (i.stopType==2L & Rank<=RTS_N & dist<=2.0)]
  
  setnames(egress_legs, "i.stop_id", "start_stops")
  setnames(egress_legs, "stop_id", "end_stops")
  setnames(egress_legs, "i.stop_lat", "start_lat")
  setnames(egress_legs, "i.stop_lon", "start_lon")
  setnames(egress_legs, "stop_lat", "end_lat")
  setnames(egress_legs, "stop_lon", "end_lon")
 
 access_legs<-access_legs[, c("start_stops" ,"end_stops", "dist"), with=FALSE]
 egress_legs<-egress_legs[, c("start_stops" ,"end_stops", "dist"), with=FALSE]
 
 AccEgr_Legs<-rbind(access_legs, egress_legs)
 AccEgr_Legs[, service_id:="Walk"]
 AccEgr_Legs[, r_type:="Walk"]
 AccEgr_Legs[, Road_Index:=0L]
 AccEgr_Legs[, stop_link_sequence:=0L]

  AccEgr_Legs[, road_edge_id:=0L]
  AccEgr_Legs[,r_service_lines:=""]
  
  AccEgr_Legs[,edge_id:=1:nrow(AccEgr_Legs)]
  AccEgr_Legs[,link_travel_time:=dist*15*60]

 
  AccEgr_Legs<-AccEgr_Legs[, c("start_stops" ,"end_stops","r_type","service_id","Road_Index","stop_link_sequence"
                                ,"road_edge_id","r_service_lines","link_travel_time","edge_id")
                            , with=FALSE]
  
  return(AccEgr_Legs)
}

