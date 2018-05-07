Buses have to travel on a road network. This codebase finds bus routes which are along
a specified SimMobility segments for a given General Transit Feed Specification (GTFS).

It has the following three parts:
1. process General Transit Feed Specification (GTFS) files
    If you have multiple GTFS files, you may want to merge them first.
    An exemplary code: clean_merge_gtfs.py.

2. find bus routes (sub routes) along SimMobility segments
   Provide SimMobility segments and following standard GTFS files:
   routes.txt, trips.txt, stop_times.txt, shapes.txt and stops.txt.

   Complete 9 step procedure in process.py.

3. create SimMobility bus tables based on connected subtrips using
   prepare_bus_tables.py.
