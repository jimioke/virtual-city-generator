


# individual variables

# people in HH: p102
# relationship to the head of household: p103 
# Delete observations without "Urban Hukou": p104
# Sex: p105
# Age, need to aggregate: p106
# Status (employment): p107
# marriage: p109
# education level: p112
# total income: p201


mydata <- read.table('21741-0001-Data.tsv', header=T, sep='\t')
dim(mydata)
colnames(mydata)
count(mydata, 'city')
plot(count(mydata,'p106'),cex=0.5)

 