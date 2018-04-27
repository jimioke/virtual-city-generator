library(MultiLevelIPF)
library(stringr)
setwd('~/Desktop/virtual-city-generator/population-synthesis/Processing_data')
getwd()

samples <- read.table("samples/RS.dat", header=TRUE)
ind <- read.table("samples/IND.dat", header=TRUE)

all_counties = counties = c(24001, 24003, 24005, 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510)

for (county in all_counties){
  county_str <- toString(county)
  age_file <- str_c("totals/", county_str, "_age.dat")
  gender_file <- str_c("totals/", county_str, "_gender.dat")
  vehicle_file <- str_c("totals/", county_str, "_vehicles.dat")

  age <- read.table(age_file, header=TRUE)
  gender <- read.table(gender_file, header=TRUE)
  vehicles <- read.table(vehicle_file, header=TRUE)
  fit_problem <- fitting_problem(ref_sample = samples,
                  field_names = special_field_names(groupId = "hhid", individualId = "indid",
                                                    count = "N"),
                  group_controls = list(age, gender, vehicles),
                  individual_controls = list(ind))

  result <- ml_fit_ipu(fit_problem)
  outputFile = str_c('multilevel_sample_weights/', county, '_multilevel_weights.csv')
  print("ok---------------------------------------------")
  #print(result["weights"])
  write.csv(result["weights"], outputFile, append=False, sep = " ")
}

