1. Filter out, clean and make consistent train GTFS files.
  1. filter out train from general GTFS files using filterTrainGTFS function
  1. find ROUTE_END using QGIS
  2. find Route_to_shapes using findLongestLines function
  3. Create consistent GTFS files using createLines function

2. Create SimMobility tables
  1. from Route_to_shapes, define Line_pair
  2. Call sequence of functions in order to generate a complete set of
     SimMobility tables.

3. upload all the tables to a proper database schema
  1. call upload.py (python2)
