
#create route segment using travel time as route segment attributes
#for each service line direction, temp[i]
#get its stop_id in sequence
#PT_routes<-rbind(train_routes, bus_routes)

Generate_SimM_Route_Segment<-function(PT_routes, Type)
{
      
    # remain just 1 trip for each service_id
    #PT_routes<-PT_routes[order(service_id, trip_id, stop_sequence)]
    setkeyv(PT_routes, c("service_id", "stop_sequence"))
    
    if(Type=="Bus")
    {
      PT_routes[,I_trip:=0L]
      PT_routes[, max_seq:=max(stop_sequence), by="service_id"]
      PT_routes[stop_sequence==max_seq,I_trip:=trip_id]
      PT_routes[, max_trip:=max(I_trip), by="service_id"]
      PT_routes<-PT_routes[trip_id==max_trip]
    }
    # remain just 1 trip for each service_id
    if(Type == "RTS")
    {
      PT_routes[,I_trip:=""]
      PT_routes[, max_seq:=max(stop_sequence), by="service_id"]
      PT_routes[stop_sequence==max_seq,I_trip:=trip_id]
      PT_routes[, max_trip:=max(I_trip), by="service_id"]
      PT_routes<-PT_routes[trip_id==max_trip]
    }
    # 387 service lines
    
    
    #convert scheduled time into minutes
    PT_routes<-PT_routes[order(service_id, trip_id, stop_sequence)]
    PT_routes[, schedule_arrival_time := as.numeric(word(arrival_time, 1, sep = fixed(':')))*3600
                                                  +as.numeric(word(arrival_time, 2, sep = fixed(':')))*60
                                                  +as.numeric(word(arrival_time, 3, sep = fixed(':')))] 
    PT_routes[, schedule_next_arrival_time := 0] 
    #PT_routes[, travel_time := 0] 
    #calculate scheduled Travel time and store at target/dest node
    #PT_routes[service_id == temp[1], 
    
    temp<-unique(PT_routes$service_id)
    for (i in 1: length(temp))
    {
      test<-PT_routes[service_id == temp[i]]$schedule_arrival_time
      for(k in 1:(length(test)-1)){test[k]=test[k+1]}
      PT_routes[service_id == temp[i]]$schedule_next_arrival_time<-test
      
    }
    
    #PT_routes[, travel_time:= schedule_next_arrival_time-schedule_arrival_time]
    PT_routes[, r_type:=Type]
  

    temp<-unique(PT_routes$service_id)
    PT_stop_link<-data.table()
    #create all stop-link
    for (i in 1: length(temp))
    {
    	test<-PT_routes[service_id == temp[i]]
    	test<-test[order(test$stop_sequence)]
    	
    	test_stop_id<-test$stop_id
    	#cat(test)
    	test_time<-test$schedule_arrival_time
    	test_seq<-test$stop_sequence
    	test_r_type<-test$r_type
    	n<-nrow(test)
    	#n_time<-length(test_time)
    	
    	service_id<-c()
    	start_stops<-c()
    	end_stops<-c()
    	start_arrival_time<-c()
    	end_arrival_time<-c()
    	Road_Index<-c()
    	stop_link_sequence<-c()
    	r_type<-c()
    	
    	for(k in 1:(n-1))  #for(i in 1:(n-1)){ for(j in 1:(n-i))
    	{ 
    			#j=1
    			service_id<-c(service_id, temp[i])
    			start_stops<-c(start_stops, test_stop_id[k])
    			end_stops<-c(end_stops, test_stop_id[k+1])
    			start_arrival_time<-c(start_arrival_time, test_time[k])
    			end_arrival_time<-c(end_arrival_time,test_time[k+1])
    			Road_Index<-c(Road_Index, "1")
    			stop_link_sequence<-c(stop_link_sequence, test_seq[k])
    			r_type<-c(r_type, test_r_type[k])
    
    	}
    	
    	temp_table<-data.table(cbind(start_stops, end_stops, start_arrival_time, end_arrival_time, r_type, service_id,Road_Index,stop_link_sequence))
    	PT_stop_link<-rbind(PT_stop_link, temp_table)
    	
    }

    #check for parallel links and combine them and assign them correct road index.
    setkeyv(PT_stop_link, c("start_stops", "end_stops"))
    PT_stop_link[,road_edge_id:=.GRP, by=key(PT_stop_link)]
    PT_stop_link[,stop_link_sequence:=as.integer(as.character(stop_link_sequence))]
    PT_stop_link[,start_arrival_time:=as.numeric(as.character(start_arrival_time))]
    PT_stop_link[,end_arrival_time:=as.numeric(as.character(end_arrival_time))]
    PT_stop_link[,start_stops:=as.character(start_stops)]
    PT_stop_link[,end_stops:=as.character(end_stops)]
    PT_stop_link[,service_id:=as.character(service_id)]
    PT_stop_link[,Road_Index:=as.character(Road_Index)]
    PT_stop_link[,road_edge_id:=as.character(road_edge_id)]
    PT_stop_link[,r_type:=as.character(r_type)]
    	
    #create all dummy links with reference to PT_stop_link
    PT_stop_seg<-c()
    temp<-unique(PT_stop_link$service_id)
    for (i in 1: length(temp))
    {
    	test<-PT_stop_link[service_id == temp[i]]
      test<-test[order(test$stop_link_sequence)]
    	test_start<-test$start_stops
    	test_end<-test$end_stops
    	#cat(test)
    	test_start_time<-test$start_arrival_time
    	test_end_time<-test$end_arrival_time
    	test_seq<-test$stop_link_sequence
    	test_roadid<-test$road_edge_id
    	test_r_type<-test$r_type
    	n<-nrow(test)
    	#n_time<-length(test_time)
    	
    	service_id<-c()
    	start_stops<-c()
    	end_stops<-c()
    	start_arrival_time<-c()
    	end_arrival_time<-c()
    	Road_Index<-c()
    	stop_link_sequence<-c()
    	road_edge_id<-c()
    	r_type<-c()
    	
    	if(n>1)
    	{
    		for(k in 1:(n-1))  #for(i in 1:(n-1)){ for(j in 1:(n-i)) # k is starting label
    		{ 	
    			
    				for(j in 1:(n-k)) # j is step length
    				{
    					service_id<-c(service_id, temp[i])
    					start_stops<-c(start_stops, test_start[k])
    					end_stops<-c(end_stops, test_end[k+j])
    					start_arrival_time<-c(start_arrival_time, test_start_time[k])
    					end_arrival_time<-c(end_arrival_time, test_end_time[k+j])
    					stop_link_sequence<-c(stop_link_sequence, test_seq[k])
    					#compute link travel time
    					#link_travel_time<-c(link_travel_time, )
    					Road_Index<-c(Road_Index, "0")
    					test_temp<-test_roadid[k]
    					r_type<-c(r_type, test_r_type[k])
    					#update road edge_id:
    					for(h in 1:j)
    					{
    						test_temp<-str_c(test_temp,"/",test_roadid[k+h])
    					}
    					
    					road_edge_id<-c(road_edge_id, test_temp)
    					
    				}
    		}
    	}
    	
    	temp_table<-data.table(cbind(start_stops, end_stops, start_arrival_time, end_arrival_time,r_type, service_id,Road_Index,stop_link_sequence,road_edge_id))
    	PT_stop_seg<-rbindlist(list(PT_stop_seg, temp_table))
    
    }
    
    #ok. de factor
    PT_stop_seg[,stop_link_sequence:=as.integer(as.character(stop_link_sequence))]
    PT_stop_seg[,start_arrival_time:=as.numeric(as.character(start_arrival_time))]
    PT_stop_seg[,end_arrival_time:=as.numeric(as.character(end_arrival_time))]
    PT_stop_seg[,start_stops:=as.character(start_stops)]
    PT_stop_seg[,end_stops:=as.character(end_stops)]
    PT_stop_seg[,service_id:=as.character(service_id)]
    PT_stop_seg[,Road_Index:=as.character(Road_Index)]
    PT_stop_seg[,road_edge_id:=as.character(road_edge_id)]
    PT_stop_seg[,r_type:=as.character(r_type)]
    
    #Need to merge #check for parallel links and combine them and assign them correct road index.
    setkeyv(PT_stop_seg, c("start_stops", "end_stops", "road_edge_id"))
    #PT_stop_seg[,edge_id:=.GRP, by=key(PT_stop_seg)]
    PT_stop_seg[,r_service_lines:=str_c(service_id, collapse="/"), by=key(PT_stop_seg)]
    
    setkeyv(PT_stop_link, c("start_stops", "end_stops", "road_edge_id"))
    #PT_stop_link[,edge_id:=.GRP, by=key(PT_stop_link)]
    PT_stop_link[,r_service_lines:=str_c(service_id, collapse="/"), by=key(PT_stop_link)]
    PT_stop_link[,link_travel_time:=end_arrival_time-start_arrival_time]
    PT_stop_link[,link_travel_time:=min(link_travel_time), by=key(PT_stop_link)]
    PT_stop_link[,start_arrival_time:=NULL]
    PT_stop_link[,end_arrival_time:=NULL]
    PT_stop_link<-unique(PT_stop_link)
    
    #process two tables seperately making sure PT_stop_link is always on top
    # get rid of duplicated rows after obtain link_travel_time
    PT_stop_seg[,link_travel_time:=end_arrival_time-start_arrival_time]
    setkeyv(PT_stop_seg, c("start_stops", "end_stops", "road_edge_id"))
    PT_stop_seg[,link_travel_time:=min(link_travel_time), by=key(PT_stop_seg)]
    PT_stop_seg[,start_arrival_time:=NULL]
    PT_stop_seg[,end_arrival_time:=NULL]
    PT_stop_seg<-unique(PT_stop_seg)
    
    #merge two table
    setkeyv(PT_stop_seg, c("start_stops", "end_stops", "road_edge_id"))
    PT_routes_seg<-rbindlist(list(PT_stop_link,PT_stop_seg))
    
    PT_routes_seg[, edge_id:=seq(1:nrow(PT_routes_seg))]
    
    return(PT_routes_seg)
}

