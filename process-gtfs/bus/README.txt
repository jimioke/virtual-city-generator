Buses have to go on road network. This codebase finds bus trips which can go
through SimMobility segments from a given General Transit Feed Specification (GTFS).

It has the following three parts:
1. process General Transit Feed Specification (GTFS) files
    If you have multiple GTFS files, you may want to merge them.
    An exemplary code: clean_merge_gtfs.py

2. find bus routes (sub routes) along SimMobility segments
   You must have SimMobility segments and following standard GTFS files:
   routes.txt, trips.txt, stop_times.txt, shapes.txt and stops.txt. Then you can
   complete 9 steps procedure in process.py

3. create SimMobility bus tables
   You can create SimMobility tables based on connected subtrips using
   prepare_bus_tables.py
