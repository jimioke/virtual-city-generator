SimM_stopsTOwalk_legs<-function(temp1,temp2, RTS_radius, Bus_radius)
{
  

  mapped_stops<-setkey(temp1[,c(k=1,.SD)],k)[temp2[,c(k=1,.SD)],allow.cartesian=TRUE][,k:=NULL]
  
  mapped_stops<-mapped_stops[stop_id!=i.stop_id]
  mapped_stops[, dist:=geodDist(stop_lon, stop_lat,i.stop_lon,i.stop_lat)]
  mapped_stops<-mapped_stops[dist<=2.0]  #665890
  # get ride of RTS to RTS

  # change to square distance, not direct
  #mapped_stops[, dist:=geodDist(stop_lon, stop_lat,stop_lon,i.stop_lat) +geodDist(stop_lon, stop_lat,i.stop_lon,stop_lat) ] 
  mapped_stops<-mapped_stops[dist<=Bus_radius | (i.stopType==2L & dist<=RTS_radius)|(stopType==2L & dist<=RTS_radius)]
  
  # generate link attributes the same as other legs
  setnames(mapped_stops, "stop_id", "start_stops")
  setnames(mapped_stops, "i.stop_id", "end_stops")
  setnames(mapped_stops, "stop_lat", "start_lat")
  setnames(mapped_stops, "stop_lon", "start_lon")
  setnames(mapped_stops, "i.stop_lat", "end_lat")
  setnames(mapped_stops, "i.stop_lon", "end_lon")
  
  mapped_stops[, service_id:="Walk"]
  mapped_stops[, Road_Index:=0L]
  mapped_stops[, stop_link_sequence:=0L]
  mapped_stops[, road_edge_id:=0L]
  mapped_stops[, r_type:="Walk"]
  mapped_stops[, r_service_lines:=""]
  mapped_stops[,link_travel_time:=dist*15*60]
  mapped_stops[,edge_id:=1:nrow(mapped_stops)]
  
  mapped_stops<-mapped_stops[, c("start_stops" ,"end_stops","r_type","service_id","Road_Index","stop_link_sequence"
                            ,"road_edge_id","r_service_lines","link_travel_time","edge_id")
                            , with=FALSE]
   
  return(mapped_stops)
}

