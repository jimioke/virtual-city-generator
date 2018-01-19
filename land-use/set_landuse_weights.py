import fiona
import re
import geopandas as gpd
import baltimore_landuse_code

fpath = 'original-landuse/landuse.shp'
# outFolder = 'process/1-population-weights/'
# outFolder = 'process-work/1-work-weights/'
outFolder = 'weights/'
inFolder = 'original_landuse_data/'
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

# df = gpd.read_file(fpath)
# df['pop_weight'] = df.apply(lambda row: pop_weight.WEIGHTS[row.LU_2008], axis=1)
#
# df.to_file(outFolder + 'population_weights.shp')
