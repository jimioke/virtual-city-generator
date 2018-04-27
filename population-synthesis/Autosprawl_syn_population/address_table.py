import pandas as pd
import geopandas as gpd
import baltimore_landuse_code
from shapely.geometry import Point

outFolder='to_db/'

DEGREE_PROJ = {'init': 'epsg:4326'}
CARTESIAN_PROJ = {'init': 'epsg:3857'}

inFolder = 'Baltimore_syn_population/'
counties = []

code_county = {
    24003 : 'AnneArundel', #24003
    24510: 'BaltimoreCity', #24510
    24005: 'BaltimoreCounty', #24005
    24013: 'Carroll', #24013
    24027: 'Howard', #24027
    24035: 'QueenAnne', #24035
    24025: 'Harford' #24025
}

def sla_address_id(inFile='grid_points/single_point/grid_points.shp', outFile=outFolder+'sla_address_id.csv'):
    # 49783 points
    # COUNTYFP10, TAZCE10, lu_code, lu_cat
    # 'id', 'taz_id', 'x_coord', 'y_coord', 'county'
    grid = gpd.read_file(inFile)
    grid['id'] = grid.index + 1
    grid['sla_postcode'] = grid['id']
    grid['x_coord'] = grid.apply(lambda row: row.geometry.x, axis=1)
    # print(grid.head)
    grid['y_coord'] = grid.apply(lambda row: row.geometry.y, axis=1)
    grid.rename(columns={'COUNTYFP10':'county', 'TAZCE10': 'taz_id'}, inplace=True)
    grid.taz_id = grid.taz_id.astype(int)
    grid.to_csv('grid_id_for_allocation.csv')

    grid = grid.filter(items=['id', 'taz_id', 'x_coord', 'y_coord', 'county', 'sla_postcode'])
    grid.to_csv(outFile, index=False)

sla_address_id()




    # 85765
