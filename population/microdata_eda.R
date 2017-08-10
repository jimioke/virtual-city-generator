

library(ipfp)
library(plyr)
library(bnlearn)
library(ggplot2)
library(data.table)
# individual variables

# household number: pcode
# people in HH: p102
# relationship to the head of household: p103 
# Delete observations without "Urban Hukou": p104
# Sex: p105
# Age, need to aggregate: p106
# Status (employment): p107
# marriage: p109
# education level: p112
# total income: p201



# household variables
# total financial assets: h401
# location of residence: h501
# current household living standard group in city: h604a


individual <- read.table('data/21741-0001-Data.tsv', header=T, sep='\t')
household <- read.table('data/21741-0002-Data.tsv', header=T, sep='\t')


# individual <- individual[individual$city == '110101']
# select people in city

households_tb_kept <- individual[individual$p104 == 1, 'pcode']
household <- subset(household, pcode %in%  households_tb_kept)
individual <- individual[individual$p104==1 & !is.na(individual$pcode),]


dim(individual)
colnames(individual)
count(individual, 'city')
plot(count(individual,'p106'),cex=0.5)


inRawData <- as.data.frame(individual[,c('pcode','p102','p103','p105','p106','p107','p109','p112','p201')])
#inRawData <- individual[,c('pcode','p105','p106','p107','p109','p112','p201')]
hhRawData <- as.data.frame(household[,c('pcode','h401','h501')])


colnames(inRawData) <- c('pcode','hh_size','rel','sex','age','emp_status','marriage','edu','inc')
colnames(hhRawData) <- c('pcode','fin_asset','loc_res')

# hh_size:
# categories: 1,2,3,4, >5
for (i in unique(inRawData$pcode)){
  inRawData[inRawData$pcode == i, 'hh_size'] <- max(inRawData[inRawData$pcode == i,'hh_size'])
}
inRawData$hh_size <- ifelse(inRawData$hh_size >= 5, 5, inRawData$hh_size)

# rel: relationship with the head of the household
# 1: self; 2:spous; 3:child; 4: grandchild; 5: parent; 6: other;
rel_raw <- list(c(1),c(2),c(3,4),c(5), c(6,7), c(8,9,10,11))
rel_ind <- list()
for (i in 1:length(rel_raw)){
  rel_ind <- c(rel_ind, list(which(inRawData$rel %in% rel_raw[[i]])))
}
for (i in 1:length(rel_raw)){
  inRawData[rel_ind[[i]],'rel'] <- i
}


# sex: male=1, female=2
# age: 0-9 = 1, 10-19 = 2, 20-29 = 3, ... 50-59 = 6, >=60 = 7
# work: 
#   1. working or employment: 1; 
#   2. student: 12
#   3. retired: 3,7,8
#   4. unemployed: 2,4,5,6,9,10,11,13
#   5. others: 14, 0, missing


inRawData$age <- ifelse(inRawData$age>=60, 7, as.integer(inRawData$age/10+1))
emp_raw <- list(c(1),c(12),c(3,7,8), c(2,4,5,6,9,10,11,13), c(14,0,NA))
emp_ind <- list()
for (i in 1:length(emp_raw)){
  emp_ind <- c(emp_ind, list(which(inRawData$emp_status %in% emp_raw[[i]])))
}
for (i in 1:length(emp_raw)){
  inRawData[emp_ind[[i]],'emp_status'] <- i
}

# Marriage: 
# Not married: 1; Married: 2;


inRawData$marriage <- ifelse(inRawData$marriage == 2, 2, 1)
inRawData <- inRawData[!is.na(inRawData$marriage), ]

# Education:
# 1. Never schooled: 1
# 2. Class for eliminating illiteracy, elementary school: 2,3
# 3. Middle schoole: 4,5
# 4. Junior College/technical school: 6,7
# 5. University/graduate: 8,9
# 6. Other: 0

edu_raw <- list(c(1),c(2,3),c(4,5),c(6,7),c(8,9),c(0,NA))
edu_ind <- list()
for (i in 1:length(edu_raw)){
  edu_ind <- c(edu_ind, list(which(inRawData$edu %in% edu_raw[[i]])))
}
for (i in 1:length(edu_raw)){
  inRawData[edu_ind[[i]],'edu'] <- i
}

# income
# 6 categories
inRawData$inc[is.na(inRawData$inc)] <- mean(inRawData$inc,na.rm = T)
inRawData$inc <- cut(inRawData$inc, breaks=c(0,5000,10000,15000,20000,30000,max(inRawData$inc,na.rm = T)),labels = 1:6,include.lowest = T)


# structure learning
for (i in 2:8){
  inRawData[,i] <- as.factor(inRawData[,i]) 
}
bn.hc <- hc(inRawData[,2:8], score='aic')
ptm <- proc.time()
bn.tb <- tabu(inRawData[,2:8], score='aic', tabu=500)
proc.time()-ptm
graphviz.plot(bn.hc)
graphviz.plot(bn.tb)
par(mfrow=c(1,2))
graphviz.compare(bn.hc, bn.tb)


# parameter learning
fitted.hc <- bn.fit(bn.hc, inRawData[,2:8], method = 'mle')
fitted.tb <- bn.fit(bn.tb, inRawData[,2:8], method = 'mle')

ptm <- proc.time()
simulation0 <- rbn(fitted.tb, 19612368,debug=T)
proc.time()-ptm

eduCompare <- melt(cbind())
ggplot(simulation0,aes(x=edu))+geom_histogram(stat='count')

# Plot barplot which compares the marginal distributions of a certain attribute
# from sample data and simulation data
plotCompareBarplot <- function(df1, df2, labs){
  Sample <- table(df1)/length(df1)
  Simulation <- table(df2)/length(df2)
  prob <- cbind(Sample, Simulation)
  df <- melt(prob,id.var = 1)
  names(df) <- c('Categories', 'Probability', 'Data')
  g <- ggplot(df, aes(x=Categories, y=Data, fill=Probability)) +
    geom_bar(stat='identity',position = position_dodge())+
    #theme(axis.text.x = element_text(angle = 90)) +
    scale_x_continuous(breaks=1:length(labs),labels = labs)
  g
  
}
# barplot in comparing the distribution of attributes
edu_labs <- c('Never', 'Primary','Middle','High','University','Other')
plotCompareBarplot(inRawData$edu, simulation0$edu, labs = edu_labs)




#inContTable <- table(inRawData[,2:dim(inRawData)[2]])
inContTable <- xtabs(~hh_size+rel+sex+age+inc+emp_status+marriage+edu,data=inRawData)

# number of types: 
# hh_size(5) * rel(6)  * sex(2) * age(7) * emp_status(5) * marriage(2) * edu(6) * inc(7)
# 188160
# this is more than the sample size, hence the problem of zero-cell is severe.
# we need larger samples.

# convert table to array

target.sex <- c(10126430, 9485938) 
target.sex.age <- c() 


 