import fiona
import re
import geopandas as gpd
import baltimore_landuse_code

counties = {
    'AnneArundel': 'Anne_2010LULC', #24003
    'BaltimoreCity': 'Baci_2010LULC', #24510
    'BaltimoreCounty': 'Baco_2010LULC', #24005
    'Carroll': 'Carr_2010LULC', #24013
    'Howard' : 'Howa_2010LULC', #24027
    'QueenAnne' : 'Quee_2010LULC', #24035
    'Harford' : 'Harf_2010LULC' #24025
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

def set_landuse_weights(inFolder='original_landuse_data/', outFile='weights/points/'):
    for key, county in countyCodes.items():
        landFile = inFolder + county + '/' + county + '.shp'
        outFile = outFolder + key + '.shp'
        df = gpd.read_file(landFile)
        # print(df.head)
        # print(df.LU_CODE.unique())
        df['pop_weight'] = df.apply(lambda row: baltimore_landuse_code.HH_WEIGHTS[row.LU_CODE], axis=1)
        df['edu_weight'] = df.apply(lambda row: baltimore_landuse_code.EDU_WEIGHTS[row.LU_CODE], axis=1)
        df['firm_weight'] = df.apply(lambda row: baltimore_landuse_code.FIRM_WEIGHTS[row.LU_CODE], axis=1)
        df['id'] = df.index + 1 # We need index starting from 1.
        df.to_file(outFile)

def clean_point_weights(inFolder='weights/points/', outFile='weights/clean/'):
    for key, county in countyCodes.items():
        raster_points = inFolder + key + '.shp'
        outFile = outFolder + key + '.shp'
        points = gpd.read_file(raster_points)
        points = points[points.value != 0]
        points.rename(columns={'value': 'TAZ'}, inplace=True)
        points['TAZ'] = points['TAZ'].astype('int')
        points.to_file(outFile)

def count_taz_points(inFolder='weights/clean/',outFile='weights/taz_num_points/'):
    for key, county in countyCodes.items():
        raster_points = inFolder + key + '.shp'
        taz_boundary = 'weights/' + key + '.shp'
        points = gpd.read_file(raster_points) # County: Raster cell point, TAZid
        taz = gpd.read_file(taz_boundary)     # County: landuse weights, TAZid --> number of cells
        taz.index = taz['id']
        taz['ncells'] = 0
        sizes = points.groupby('TAZ').size()
        for parentTAZ, size in sizes.iteritems():
            taz.set_value(parentTAZ, 'ncells', size)
        taz.to_file(outFile + key + '.shp')

count_taz_points()
