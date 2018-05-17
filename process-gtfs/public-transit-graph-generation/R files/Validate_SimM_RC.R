#validate simM_routeChoice

path_stats<-fread("~/SimMobility Demo/paths.csv", header=TRUE)
path_stats[, wait_time:=total_waiting_time/60]
path_stats[, walk_time:=total_walking_time/60]
path_stats[, wait_time:=total_waiting_time/60]
path_stats[, transit_time:=total_invehicle_secs/60]

attr_list<-c("transit_time", "walk_time", "wait_time", "total_number_of_transfers", "total_cost", "path_size")

#local beta_in_vehicle = -0.35
# local beta_walk = -0.65
# local beta_wait = -0.46
# local beta_no_txf= -4.31
# local beta_cost = -0.16
# local beta_path_size = 0.8
param_in<-matrix(c(-0.35,-0.65,-0.46,-4.31,-0.16,0.8), ncol=1)

path_stats[, utility:=param_in[1]*transit_time+param_in[2]*walk_time+param_in[3]*wait_time
            +param_in[4]*total_number_of_transfers+param_in[5]*total_cost+param_in[6]*logb(path_size)]

setkeyv(path_stats, "pathset_id")
path_stats[, e_uti:=exp(utility)]
path_stats[, total_e_uti:=sum(e_uti), by="pathset_id"]
path_stats[,prob:=e_uti/total_e_uti]


