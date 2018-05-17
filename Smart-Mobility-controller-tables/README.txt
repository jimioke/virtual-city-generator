This example illustrates how to create parking, taxi_fleet and taxi_stand tables
based on road network and TAZ divisions.

Example city: Baltimore

1. Find in which taz nodes and segments are (using QGIS)
2. Create SimMobility tables using prepare.py
   You can investigate created parking, taxi_fleet and taxi_stand locations
   using (QGIS) MMQGIS > Import/Export > Geometry import from CSV file
3. Upload to the database using upload.py (python2)
