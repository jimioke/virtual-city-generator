#simPSlogit_getProb.R 
#input: parameter to estimate row matrix
# input: CS_path_attr: paths contains path stats and observed freqencies
		# path_size always stores the path_size, freq always stores the observed frequency
# attr_list: list of path attributes as estimation inputs
   ----#path size in log(pathsize) as one of the attribute
#--output: paths with probability


simPSlogit_getProb<-function(param, CS_path_attr, attr_list)
{

	#---generate r_var1 to r_var4 based on param[17:20]
	# add attr_list to store variable names

	N_beta<-length(attr_list)
	beta_coeff<-param[1:N_beta]
	
	N<-nrow(CS_path_attr)
	setkeyv(CS_path_attr, c("ptPathSetId"))

	temp<-as.matrix(CS_path_attr[,c(attr_list), with=FALSE])
	
	CS_path_attr$chosen_utility<-temp%*%beta_coeff

	#-----------------------------N*N_beta--N_beta*1


	CS_path_attr[, denorm:=sum(exp(chosen_utility)), by=key(CS_path_attr)]
	CS_path_attr[, prob:=exp(chosen_utility)/denorm]

	return(CS_path_attr)
}

