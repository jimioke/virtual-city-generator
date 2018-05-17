This repository provides tools and examples for generating a city's population,
road network and many other SimMobility tables.

Each of these following folders how detailed instructions on how to use

###network-from-OSM
  build SimMobility road network from OpenStreetMap
###process-gtfs
  Process bus and train GTFS files on the top of road network
  Create a public transit graph (merging road network, bus and train stops)
###population-synthesis
  synthesize population using MultilevelIPF
###taz-use
  Grid and create address points
  Allocate population totals over grid point address
###Smart-Mobility-controller-tables
  Create parking, taxi_fleet and taxi_stand tables/
