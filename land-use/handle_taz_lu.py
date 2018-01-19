import fiona
import re
import pandas as pd
import geopandas as gpd
import baltimore_landuse_code
import fiona

counties = {
    'AnneArundel': 'Anne_2010LULC', #24003
    'BaltimoreCity': 'Baci_2010LULC', #24510
    'BaltimoreCounty': 'Baco_2010LULC', #24005
    'Carroll': 'Carr_2010LULC', #24013
    'Howard' : 'Howa_2010LULC', #24027
    'QueenAnne' : 'Quee_2010LULC', #24035
    'Harford' : 'Harf_2010LULC' #24025
}

code_county = {
    '003': 'AnneArundel', #24003
    '510': 'BaltimoreCity', #24510
    '005': 'BaltimoreCounty', #24005
    '013': 'Carroll', #24013
    '027' : 'Howard', #24027
    '035' : 'QueenAnne', #24035
    '025' : 'Harford' #24025
}

countyCodes = {
    '24003': 'Anne_2010LULC', #24003
    '24510': 'Baci_2010LULC', #24510
    '24005': 'Baco_2010LULC', #24005
    '24013': 'Carr_2010LULC', #24013
    '24027' : 'Howa_2010LULC', #24027
    '24035' : 'Quee_2010LULC', #24035
    '24025' : 'Harf_2010LULC' #24025
}
DEGREE_PROJ = {'init': 'epsg:4326'}
CARTESIAN_PROJ = {'init': 'epsg:3857'}
# Land-use crs = {'proj': 'lcc', 'lat_1': 38.3, 'lat_2': 39.45, 'lat_0': 37.66666666666666, 'lon_0': -77, 'x_0': 400000, 'y_0': 0, 'datum': 'NAD83', 'units': 'm', 'no_defs': True}

outFolder = 'TAZ_LU_samples/'
original_TAZ_file = 'SOURCES/2010_Traffic_Analysis_Zones_TAZ_CensusTIGER/2010_Traffic_Analysis_Zones_TAZ_CensusTIGER.shp'
TAZ_boundry_file = '2010_TAZ/staz_crs4326.shp'
LU_code_folder = 'SOURCES/original_landuse_data/'
LU_CATEGORY = set(baltimore_landuse_code.CLASSIFICATION_STR.values())

def merge_dfs(all_gdf, outFile, projection):
    all_taz = gpd.GeoDataFrame( pd.concat( all_gdf, ignore_index=True) )
    all_taz['id'] = all_taz.index + 1
    all_taz.crs = projection #fiona.crs.from_epsg(4326)
    all_taz.to_file(outFile)
    return all_taz


def set_landuse_file(inFolder=LU_code_folder, outFile=outFolder+'merged_lu_crs4326.shp', projection=DEGREE_PROJ):
    """Merge land use files.

    Take land use data (all counties) from the specified input folder and
    merge and write them into one file with a specified projection.
    """
    dfs = []
    global_crs = None
    for key, county in countyCodes.items():
        landFile = inFolder + county + '/' + county + '.shp'
        df = gpd.read_file(landFile)
        df['county'] = key
        df = df.to_crs(projection)
        dfs.append(df)
    merge_dfs(dfs, outFile, projection)
# set_landuse_weights()

def set_taz_boundary_file(inFile=original_TAZ_file, outFolder=outFolder, proj=DEGREE_PROJ):
    df = gpd.read_file(inFile)
    df = df.to_crs(proj)
    df.to_file(outFolder + 'taz_crs4326.shp')
# set_taz_boundary_file()

def count_lu_in_taz(inFile=outFolder + 'lu_points_in_taz.shp',outFile=outFolder+'lu_category_count'):
    """ Count each type of land use points(grid) in each TAZ.
    """
    lu_samples = gpd.read_file(inFile)
    lu_samples['value'] = lu_samples['value'].astype('int')
    lu_samples.rename(columns={'value': 'lu_code'}, inplace=True)
    lu_samples['lu_category'] = lu_samples.apply(lambda row: baltimore_landuse_code.CLASSIFICATION_STR[row.lu_code], axis=1)

    taz_original = gpd.read_file(TAZ_boundry_file)
    taz_original.index = taz_original.GEOID10

    for lu_cat in LU_CATEGORY:
        taz_original[str(lu_cat)] = 0

    groupedLU = lu_samples.groupby(['GEOID10', 'lu_category']).size()
    for taz_lu, size in groupedLU.iteritems():
        taz, lu = taz_lu
        taz_original.set_value(taz, str(lu), size)
    taz_original.to_csv(outFile+'.csv')
    taz_original.to_file(outFile+'.shp')

def column_head(col):
    """Find shapefile column heads"""
    if len(col) > 10:
        return col[:10]
    return col

def county_stats(inFile=outFolder+'lu_category_count.shp', outFile=outFolder+'county_lu_stats.csv'):
    # total number of points
    taz_full = gpd.read_file(inFile)
    taz_full['num_points'] = 0
    lu_column_heads = [column_head(lu_cat) for lu_cat in LU_CATEGORY]
    for lu_cat in lu_column_heads:
        taz_full['num_points'] = taz_full['num_points'] + taz_full[lu_cat]
    counties = taz_full.groupby(by=['COUNTYFP10']).sum()
    counties.to_csv(outFile)

county_stats()
