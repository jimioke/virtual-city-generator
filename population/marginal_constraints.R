
a <- t(read.table('sex_age'))
a <- cbind(a, rep(0:22,each=3))
a <- cbind(a, rep(0:2,23))

a <-data.frame(a)
colnames(a) <- c('pop','age_category','sex')
b <- a[a$age_category!=0 & a$sex!=0,]

b[3,'pop'] <- b[3,'pop']+b[1,'pop']
b[4,'pop'] <- b[4,'pop']+b[2,'pop']
b <- b[-c(1,2),]

sex_age <- array(NA, c(7,2))
for (i in 1:6){
  sex_age[i,1] <-b[4*i-3,1]+b[4*i-1,1]
  sex_age[i,2] <-b[4*i-2,1]+b[4*i,1] 
}

sex_age[7,1] <- sum(b[c((12:20)*2+1),1])
sex_age[7,2] <- sum(b[c((13:21)*2),1])


sd <- t(read.table('sex_edu'))
sd <- t()