# this is main file to estimate a route choice model using path-size logit
#----load packages-----
library("stringr", lib.loc="~/R/win-library/3.2")
library("oce", lib.loc="~/R/win-library/3.2")
library("data.table", lib.loc="~/R/win-library/3.2")

#==================INPUT FILES===========================
#  1) # ---------input folder dir
local_dir<-str_c("C:/users/fm01/Desktop/SimMobility Demo/")
#  2)  #paths_stats file with path attributes for each path in the choice set---  
path_stats_dir<-str_c(local_dir, "Model Estimation/sim_pathset_stats.csv")
#===============================================================

#=================OUTPUT FILES===========================
#1) estiamtion and stats stored in result_file
result_file<-str_c(local_dir, "Model Estimation/estimation_result.txt")
  #output data includes:
   #1.1) estimated coefficient with standard error and t-stats
   #1.2) initial loglikelihood ll0
   #1.3) final loglikelihood ll_final
   #1.4) computed likelihood ratio
   #1.5) computed rho_squared
   #1.6) computed ajusted rho_squared
   #1.7) correlation of parameters
#===============================================================


#---load functions PSL----
source("C:/users/fm01/Desktop/SimMobility Demo/R files/PSlogit_V5.R")

#---load path_stats data 
path_stats<-fread(path_stats_dir, header=TRUE)

# list down attributes for route choice model estimation  X_i
attr_list<-c("total_in_vehicle_time"
             , "total_walk_time"
             , "total_wait_time"
             , "total_no_txf"
             , "total_cost"
             , "total_path_size")
N_beta=length(attr_list)

# specify where the observed_frequency of each paths
freq_spe<-"obs_freq"

# specify where the choice set idenfier is
CS_ID<-"ptPathSetId"

# initial parameter ---N_beta*1-------
param_in<-matrix(0, nrow=N_beta, ncol=1)

# to estimate a route choice model using observed data set with path attributes in path_stats
# all output are stored in the pre-defined result file
sink(file=result_file, append=TRUE)
{
system.time(starttemp <- optim(param_in, PSlogit_V5, CS_path_attr=path_stats,
                               attr_list = attr_list,  freq_spe=freq_spe,
                               method="BFGS", control=list(trace=TRUE, REPORT=1), hessian = TRUE))

#compute path attribute * parameter utility_i=X_i*beta
path_stats$chosen_utility<-as.matrix(path_stats[,c(attr_list), with=FALSE])%*%starttemp$par
#--------------------N*(N_beta) %*% N_beta*1

# compute sum(exp(chosen_utility)) as denominator
path_stats[, denorm:=sum(exp(chosen_utility)), by=CS_ID]
# compute probability
path_stats[, prob:=exp(chosen_utility)/denorm]

#--compute invsere of hessian
inverted_temp<- solve(starttemp$hessian)
#--compute standard error, t-stats
temp_result <- cbind(starttemp$par, sqrt(diag(inverted_temp)), starttemp$par/sqrt(diag(inverted_temp)))
colnames(temp_result) <- c("Coefficient", "Std. Err.", "t")
rownames(temp_result) <- attr_list

#--compute other statistics
temp_result_stats<-matrix(0.0, nrow=5)
rownames(temp_result_stats)<-c("LL0", "LL_Final", "Likelihood_Ratio", "rho_squared", "adj_rho_squared")
temp_result_stats[1]<--PSlogit_V5(param_in, path_stats[1:nrow(path_stats)],attr_list,freq_spe)
temp_result_stats[2]<--starttemp$value
temp_result_stats[3]<--2*(temp_result_stats[1]-temp_result_stats[2])
temp_result_stats[4]<-(temp_result_stats[1]-temp_result_stats[2])/temp_result_stats[1]
temp_result_stats[5]<-(temp_result_stats[1]-temp_result_stats[2]+N_beta)/temp_result_stats[1]


#compute correlation between parameters
sd_beta<-sqrt(diag(abs(inverted_temp)))
corr_beta<-data.table(CJ(attr_list, attr_list, sorted=FALSE))
setnames(corr_beta, "V1", "beta1")
setnames(corr_beta, "V2", "beta2")
corr_beta[,beta_cov:=0.0]
corr_beta[,beta_cor:=0.0]
#corr_beta<-corr_beta[beta1!=beta2]
for(i in 1:length(attr_list))
{
  for(j in 1:length(attr_list))
  {
    corr_beta[i*j, beta_cov:=inverted_temp[i,j]]
    corr_beta[i*j, beta_cor:=inverted_temp[i,j]/(sd_beta[i]*sd_beta[j])]
  }
}

corr_beta<-corr_beta[beta1!=beta2]
#-------------------------------
cat("----------Estimates---------\n")
print(temp_result)
cat("----------stats----------\n")
print(temp_result_stats)
cat("-----------correlation of parameters-----------\n")
print(corr_beta)
}
sink()



