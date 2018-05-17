#PSlogit_V5.R
#input: parameter to estimate row matrix
# input: CS_path_attr: path attributs contains path stats and freqencies
# attr_list: list of path attributes as estimation inputs
    #path_size is part of attr_list, it comes in after taking logrithm

# freq_spe: string indicate which observed freqency to use

PSlogit_V5<-function(param, CS_path_attr, attr_list, freq_spe)
{
	# setkey for input data by each choice set
  setkeyv(CS_path_attr, CS_ID)
  
  #compute path attribute * parameter utility_i=X_i*beta
	CS_path_attr$chosen_utility<-as.matrix(CS_path_attr[,c(attr_list), with=FALSE])%*%param
	                    #--------------------N*(N_beta) %*% N_beta*1
	
	
	# for MNL;
	    # P(i)=exp(utility_i)/sum(exp(utility_j)) over the choice set
	
      # compute sum(exp(chosen_utility)) as denominator
    	CS_path_attr[, denorm:=sum(exp(chosen_utility)), by=CS_ID]
    	# compute probability
    	CS_path_attr[, prob:=exp(chosen_utility)/denorm]
	
  # compute ll_n =log(prob^obs_freq)
	CS_path_attr[, loglikeli:=get(freq_spe)*logb(prob)]
	
	# compute ll=sum(ll_n)
	LL<-sum(CS_path_attr$loglikeli)
	return(-LL)
}

