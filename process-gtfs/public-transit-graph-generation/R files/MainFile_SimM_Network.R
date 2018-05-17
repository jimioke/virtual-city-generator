#Main File to generate SimMobility network

#----load packages-----
#library("stringr", lib.loc="/usr/local/lib/R/site-library")
#library("oce", lib.loc="/usr/local/lib/R/site-library")
#library("data.table", lib.loc="/usr/local/lib/R/site-library")

library("stringr")
library("oce")
library("data.table")

#==================INPUT FILES===========================
#  1) #----------update version number here for different back of data
    #create a folder named after version
  vs<-"31Mar18"
#  2) # ---------input folder dir
  local_dir<-str_c("~/Desktop/virtual-city-generator/process-gtfs/public-transit-graph-generation/", vs, "/")
#  3)  #origin and destination nodes file---
  local_P_nodes_dir<-str_c(local_dir, "P_nodes","_", vs, ".csv")
#  4) # Bus stop file
  Bus_stops_dir<-str_c(local_dir, "SimM_bus_stops_", vs, ".csv")
#  5) RTS stop file
  RTS_stops_dir<-str_c(local_dir, "SimM_RTS_stops_", vs, ".csv")
# 6) Bus routes file (schedule, seq)
  bus_routes_dir<-str_c(local_dir, "bus_journeytime_", vs, ".csv")
# 7) RTS routes file (schedule, seq)
  RTS_routes_dir<-str_c(local_dir, "weekday_train_seq_", vs, ".csv")
#===============================================================

#=================OUTPUT FILES===========================
#1) Network with bus only -- Links
  All_bus_links_dir<-str_c(local_dir, "All_bus_links_", vs, ".csv")
#2) Network with bus only -- Stops
  All_bus_stops_dir<-str_c(local_dir, "All_bus_stops_", vs, ".csv")
# 3) Network with Bus and RTS --- Links
  All_PT_links_dir<-str_c(local_dir, "All_PT_links_", vs, ".csv")
# 4) Network with Bus and RTS -- stops
  All_PT_stops_dir<-str_c(local_dir, "All_PT_stops_", vs, ".csv")
# 5) Intermediate files for future update and correction
  #---|
    # 5.1)  bus route segment files
      Bus_routes_seg_dir<-str_c(local_dir, "SimM_bus_routes_seg_", vs, ".csv")
    # 5.2) bus transfer walk files
      Bus_txfWalk_dir<-str_c(local_dir, "Bus_txfWalk_", vs, ".csv")
    # 5.3) acces and egress files to Bus stops
      AccEgr_Bus_dir<-str_c(local_dir, "AccEgr_Bus_", vs, ".csv")
    # 5.4)  RTS route segment files
      RTS_routes_seg_dir<-str_c(local_dir, "SimM_RTS_routes_seg_", vs, ".csv")
    #  5.5) RTS transfer walks
      RTS_txfWalk_dir<-str_c(local_dir, "RTS_txfWalk_", vs, ".csv")
    # 5.6) access and egress links to RTS stations
      AccEgr_RTS_dir<-str_c(local_dir, "AccEgr_RTS_", vs, ".csv")
    # 5.7) transfer between bus stops and RTS stations
      RTS_Bus_txfWalk_dir<-str_c(local_dir, "RTS_Bus_txfWalk_", vs, ".csv")

#==========================================================

#-----prepare SimMobility network -- generate intermediat output 5.1-5.7
source("~/Desktop/virtual-city-generator/process-gtfs/public-transit-graph-generation/R files/Prepare_SimM_Network.R")

#----build simmobility network --- generate output 1-4
source("~/Desktop/virtual-city-generator/process-gtfs/public-transit-graph-generation/R files/Build_SimM_Network.R")
