import pandas as pd
import geopandas as gpd
import baltimore_landuse_code

outFolder='to_db/'
# Land use: lu_code (type_id), taz, county
# Land_use_type: id, type_id, name, description

def land_use_type(outFile=outFolder+'land_use_type.csv'):
    #id, type_id, name, description
    labels = ['id', 'type_id', 'name']
    all_lu = set()
    categories = set(baltimore_landuse_code.CLASSIFICATION.keys())
    for lu in categories:
        num_id = baltimore_landuse_code.CLASSIFICATION[lu]
        str_id = baltimore_landuse_code.CLASSIFICATION_STR[lu]
        all_lu.add( (num_id, num_id, str_id) )
    df = pd.DataFrame.from_records(list(all_lu), columns=labels)
    df = df.sort_values(by='type_id')
    df.to_csv(outFile, index=False)

def land_use(inFile='lu/merged_lu_crs4326.shp', outFile=outFolder+'land_use_zone.csv'):
    lu_zones = gpd.read_file(inFile) # LU_CODE, county, id --> Land use: lu_code (type_id)
    lu_zones['type_id'] = lu_zones.apply(lambda row: baltimore_landuse_code.CLASSIFICATION[row.LU_CODE], axis=1)
    # lu_zones['gpr'] = 'none'
    lu_zones.drop(['LU_CODE', 'county', 'geometry'], axis=1, inplace=True)
    lu_zones.to_csv(outFile, index=False)
# land_use_type()
# land_use()

def taz(inFile='taz/lu_category_count.shp', outFile=outFolder+'taz.csv'):
    # GEOID10,OBJECTID,STATEFP10,COUNTYFP10,MPOCE10,TADCE10,TAZCE10,GEOID10,MTFCC10,FUNCSTAT10,ALAND10,AWATER10,INTPTLAT10,INTPTLON10,SHAPE_STAr,SHAPE_STLe,TZ_NUM,TZ_TXT,Shape_ST_1,Shape_ST_2,TAZnum,Shape_Leng,Shape_Area,geometry,water,openLand,indust,highR,forest,lowR,commer,edu,mediumR,urbanOL,sparseR,trans,agricul
    taz = gpd.read_file(inFile)
    taz = taz.filter(items=['TAZCE10', 'Shape_Area'])
    taz.rename(columns= {'TAZCE10':'id', 'Shape_Area':'area'}, inplace=True)
    # taz.id = taz.id.astype(int)
    taz.to_csv(outFile, index=False)
# taz()
    # id, area, county
