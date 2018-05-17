Public transit graph generation
Wiki: https://github.com/smart-fm/simmobility/wiki/Public-transit-graph-generation


It is some helper functions for creating public transit graph
1. Get P_nodes_.csv, SimM_bus_stops_.csv, SimM_RTS_stops_.csv tables from the
  database using prepare.py: get_from_db().

  You must have weekday_train_seq_.csv and bus_journeytime_.csv files.
  These can be generated through bus and train GTFS processes.

  Using test.py, you can investigate your input files.

2. install following R packages
  install.packages('data.table', repos='http://cran.rstudio.com/', type="source")
  install.packages('stringr', repos='http://cran.rstudio.com/', type="source")
  install.packages('oce', repos='http://cran.rstudio.com/', type='source')

3. Run the R-script
  setwd(".../public-transit-graph-generation/R files/")
  source("MainFile_SimM_Network.R")

4. You can upload generated graph to pt_edge and pt_vertex tables using
  upload_toDb.py script.
