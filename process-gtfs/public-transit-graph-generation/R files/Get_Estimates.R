# get_estimates.R
# input1: path_stats, path_stats used for estimation
# input 2: attr_list: list of path attributes names,
# PS_in, specify whether Path_size will be included or not
get_estimates<-function(path_stats, attr_list, PS_in, freq_spe)
{
	N_beta=length(attr_list)
	param_in<-matrix(0, nrow=N_beta, ncol=1)
#~ 	system.time(startmnl <- optim(param_in, PSlogit.lf_V5, CS_path_attr=path_stats, 
#~ 		attr_list = attr_list, PS_in=PS_in,freq_spe=freq_spe,
#~ 		method="Nelder-Mead", control=list(trace=TRUE, REPORT=1, maxit=1000)))

	system.time(starttemp <- optim(param_in, PSlogit.lf_V5, CS_path_attr=path_stats,
		attr_list = attr_list, PS_in=PS_in, freq_spe=freq_spe,
		method="BFGS", control=list(trace=TRUE, REPORT=1), hessian = TRUE))
	
	temp_value<-path_stats[,get(attr_list[1])]
	for(i in 2:N_beta)
	{
		temp_value<-cbind(temp_value, path_stats[,get(attr_list[i])])
	}
	
	path_stats$chosen_utility<-temp_value%*%starttemp$par
	if(PS_in==1L)
	{
		path_stats[, chosen_utility:=chosen_utility+logb(path_size)]
	}
	#-----------------------------N*N_beta--N_beta*1

	path_stats[, denorm:=sum(exp(chosen_utility)), by=key(path_stats)]
	path_stats[, prob:=exp(chosen_utility)/denorm]

  setkeyv(path_stats, "record_id")
  path_stats[, prob_on_record:=sum(prob), by=key(path_stats)]
  path_stats<-unique(path_stats)

#-------compute the stimated probability v.s observed probability.
setkeyv(path_stats, c("origin", "dest"))
path_stats[, total_freq:=sum(get(freq_spe)), by=key(path_stats)]
path_stats[, obs_prob:=get(freq_spe)/total_freq]

path_stats[, min_prob:=min(obs_prob, prob_on_record), by=1:nrow(path_stats)]
path_stats[, max_prob:=max(obs_prob, prob_on_record), by=1:nrow(path_stats)]

#path_stats[, CR:=sum(min_prob)/sum(max_prob), by=key(path_stats)]

#CR<-mean(unique(path_stats)$CR)
	
	inverted_temp<- solve(starttemp$hessian)
	temp_result <- cbind(starttemp$par, sqrt(diag(inverted_temp)), starttemp$par/sqrt(diag(inverted_temp)))
	 colnames(temp_result) <- c("Coefficient", "Std. Err.", "z")
	rownames(temp_result) <- attr_list
 # temp_result[4,1]<-temp_result[4,1]
  #temp_result[5,1]<--temp_result[5,1]
 # temp_result[6, 3]<-10+temp_result[6,3]
	temp_result_stats<-matrix(0.0, nrow=6)
	rownames(temp_result_stats)<-c("LL0", "Ltemp", "Likelihood_Ratio", "rho_squared", "adj_rho_squared", "CR")
	temp_result_stats[1]<--PSlogit.lf_V5(param_in, path_stats[1:nrow(path_stats)],attr_list, PS_in,freq_spe)
	temp_result_stats[2]<--starttemp$value
	temp_result_stats[3]<--2*(temp_result_stats[1]-temp_result_stats[2])
	temp_result_stats[4]<-(temp_result_stats[1]-temp_result_stats[2])/temp_result_stats[1]
	temp_result_stats[5]<-(temp_result_stats[1]-temp_result_stats[2]+N_beta)/temp_result_stats[1]
 # temp_result_stats[6]<-CR

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
	print(temp_result)
	setkeyv(path_stats, "record_id")
	print(sum(unique(path_stats)[,get(freq_spe)]))
	print(temp_result_stats)
	
	
	return(starttemp$par)
		
}

#---estimate tt first, then based on the estimates, split tt into piecewise linear
get_estimates_V2<-function(path_stats, N_beta, param_in, attr_list, PS_in, freq_spe)
{
#~ 	N_beta=length(attr_list)
#~ 	param_in<-matrix(0, nrow=N_beta, ncol=1)
#~ 	system.time(startmnl <- optim(param_in, PSlogit.lf_V5, CS_path_attr=path_stats, 
#~ 		attr_list = attr_list, PS_in=PS_in,freq_spe=freq_spe,
#~ 		method="Nelder-Mead", control=list(trace=TRUE, REPORT=1, maxit=1000)))

	LL0<--PSlogit.lf_V5(param_in, path_stats,attr_list,PS_in,freq_spe)
	system.time(starttemp <- optim(param_in, PSlogit.lf_V5, CS_path_attr=path_stats,
		attr_list = attr_list, PS_in=PS_in, freq_spe=freq_spe,
		method="BFGS", control=list(trace=TRUE, REPORT=1), hessian = TRUE))
	
	temp<-path_stats[,get(attr_list[1])]
	for(i in 2:N_beta)
	{
		temp<-cbind(temp, path_stats[,get(attr_list[i])])
	}
	
	path_stats$chosen_utility<-temp%*%starttemp$par
	if(PS_in==1L)
	{
		path_stats[, chosen_utility:=chosen_utility+logb(path_size)]
	}
	#-----------------------------N*N_beta--N_beta*1

	path_stats[, denorm:=sum(exp(chosen_utility)), by=key(path_stats)]
	path_stats[, prob:=exp(chosen_utility)/denorm]
	
	inverted_temp<- solve(starttemp$hessian)
	temp_result <- cbind(starttemp$par, sqrt(diag(inverted_temp)), starttemp$par/sqrt(diag(inverted_temp)))
	 colnames(temp_result) <- c("Coefficient", "Std. Err.", "z")
	rownames(temp_result) <- attr_list
	temp_result_stats<-matrix(0.0, nrow=5)
	rownames(temp_result_stats)<-c("LL0", "Ltemp", "Likelihood_Ratio", "rho_squared", "adj_rho_squared")
	temp_result_stats[1]<-LL0
	temp_result_stats[2]<--starttemp$value
	temp_result_stats[3]<--2*(temp_result_stats[1]-temp_result_stats[2])
	temp_result_stats[4]<-(temp_result_stats[1]-temp_result_stats[2])/temp_result_stats[1]
	temp_result_stats[5]<-(temp_result_stats[1]-temp_result_stats[2]+N_beta)/temp_result_stats[1]

	
	print(temp_result)
	setkeyv(path_stats, "record_id")
	print(sum(unique(path_stats)[,get(freq_spe)]))
	print(temp_result_stats)
	
	
	return(starttemp$par)
		
}


#-------------------------17Nov14---------------------------
##---estimate tt first, then based on the estimates, split tt into N piecewise linear
get_estimates_split<-function(path_stats, N_beta, param_in, total_attr_list, split_list, PS_in, freq_spe, N_split)
{
  #~   N_beta=length(attr_list)
  #~ 	param_in<-matrix(0, nrow=N_beta, ncol=1)
  #~ 	system.time(startmnl <- optim(param_in, PSlogit.lf_V5, CS_path_attr=path_stats, 
  #~ 		attr_list = attr_list, PS_in=PS_in,freq_spe=freq_spe,
  #~ 		method="Nelder-Mead", control=list(trace=TRUE, REPORT=1, maxit=1000)))
    
 # get_estimates(path_stats, N_beta, param_in, attr_list, PS_in, freq_spe)
  LL0<-PSlogit.lf_V6(param_in, CS_path_attr, total_attr_list, split_list, PS_in, freq_spe, N_split)
  system.time(starttemp <- optim(param_in, PSlogit.lf_V6, CS_path_attr=path_stats,
                                 total_attr_list = total_attr_list, split_list= split_list, PS_in=PS_in, freq_spe=freq_spe, N_split=N_split,
                                 method="BFGS", control=list(trace=TRUE, REPORT=1), hessian = TRUE))
  N_total<-length(param_in)
  
  temp<-path_stats[,get(total_attr_list[1])]
  for(i in 2:N_beta)
  {
    temp<-cbind(temp, path_stats[,get(total_attr_list[i])])
  }
  
  path_stats$chosen_utility<-temp%*%(starttemp$par[N_split:N_total])
  if(PS_in==1L)
  {
    path_stats[, chosen_utility:=chosen_utility+logb(path_size)]
  }
  #-----------------------------N*N_beta--N_beta*1
  
  path_stats[, denorm:=sum(exp(chosen_utility)), by=key(path_stats)]
  path_stats[, prob:=exp(chosen_utility)/denorm]
  
  inverted_temp<- solve(starttemp$hessian[N_split:N_total, N_split:N_total])
  temp_result <- cbind(starttemp$par[N_split:N_total], sqrt(diag(inverted_temp)), starttemp$par[N_split:N_total]/sqrt(diag(inverted_temp)))
  colnames(temp_result) <- c("Coefficient", "Std. Err.", "z")
  rownames(temp_result) <- total_attr_list
  temp_result_stats<-matrix(0.0, nrow=5)
  rownames(temp_result_stats)<-c("LL0", "Ltemp", "Likelihood_Ratio", "rho_squared", "adj_rho_squared")
  temp_result_stats[1]<-LL0
  temp_result_stats[2]<--starttemp$value
  temp_result_stats[3]<--2*(temp_result_stats[1]-temp_result_stats[2])
  temp_result_stats[4]<-(temp_result_stats[1]-temp_result_stats[2])/temp_result_stats[1]
  temp_result_stats[5]<-(temp_result_stats[1]-temp_result_stats[2]+N_beta)/temp_result_stats[1]
  
  temp_split_result<-starttemp$par[1:(N_split-1)]
  names(temp_split_result) <- c(str_c("range", seq(1,(N_split-1), 1)))
  
  print(temp_result)
  setkeyv(path_stats, "record_id")
  print(sum(unique(path_stats)[,get(freq_spe)]))
  print(temp_result_stats)
  
  print(temp_split_result)
  
  
  return(starttemp$par)
  
}