


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
individual <- individual[individual$p104==1,]

dim(individual)
colnames(individual)
count(individual, 'city')
plot(count(individual,'p106'),cex=0.5)


inRawData <- individual[,c('pcode','p102','p105','p106','p107','p109','p112','p201')]
hhRawData <- household[,c('pcode','h401','h501')]


colnames(inRawData) <- c('pcode','num_in_hh','sex','age','emp_status','marriage','edu','inc')
colnames(hhRawData) <- c('pcode','fin_asset','loc_res')

# sex: male=1, female=2
# age: 0-9 = 1, 10-19 = 2, 20-29 = 3, ... 50-59 = 6, >=60 = 7
# work: 
#   1. working or imployment: 1; 
#   2. student: 12
#   3. unable to work: 4
#   4. retired: 3,7,8
#   5. unemployed: 2,5,6,9,
#   6. full-time homemaker: 11
#   7. wait for job assignment: 10,13
#   8. others: 14, 0
#   9. missing

inRawData$age <- ifelse(inRawData$age>=60, 7, as.integer(inRawData$age/10+1))
emp_raw <- list(c(1),c(12),c(4),c(3,7,8), c(2,5,6,9), c(11), c(10,13), c(14,0))
emp_ind <- list()
for (i in 1:length(emp_raw)){
  emp_ind <- c(emp_ind, list(which(inRawData$emp_status %in% emp_raw[[i]])))
}
for (i in 1:length(emp_raw)){
  inRawData[emp_ind[[i]],'emp_status'] <- i
}

# Marriage: 
# Never married: 1, with spous: 2, divorced: 3
# widow or widower: 4, other: 0,5  = 5, missing: NA

inRawData$marriage <- ifelse(inRawData$marriage == 0, 5, inRawData$marriage)


# Education:
# 1. Never schooled: 1
# 2. Class for eliminating illiteracy, elementary school: 2,3
# 3. Middle schoole: 4,5
# 4. Junior College/technical school: 6,7
# 5. University/graduate: 8,9
# 6. Other: 0

mrg_raw <- list(c(1),c(2,3),c(4,5),c(6,7),c(8,9),c(0))
mrg_ind <- list()
for (i in 1:length(mrg_raw)){
  mrg_ind <- c(mrg_ind, list(which(inRawData$marriage %in% mrg_raw[[i]])))
}
for (i in 1:length(mrg_raw)){
  inRawData[mrg_ind[[i]],'marriage'] <- i
}

# income
# 
inc_range <- array(NA,c(7,2))
inc_range[1,] <- c(0, 5000)
inc_range[2,] <- c(5000, 10000)
inc_range[3,] <- c(10000, 15000)
inc_range[4,] <- c(15000, 20000)
inc_range[5,] <- c(20000, 30000)
inc_range[6,] <- c(30000, 50000)
inc_range[7,] <- c(50000, max(inRawData$inc,na.rm = T)+1)

for (i in 1:dim(inc_range)[1]){
  inRawData$inc <- replace(inRawData$inc, inRawData$inc >= inc_range[i,1] & inRawData$inc < inc_range[i,2],i)
}

inContTable <- table(inRawData[,2:dim(inRawData)[2]])



 