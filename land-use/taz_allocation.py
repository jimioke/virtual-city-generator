from pulp import *
import pandas as pd
import geopandas as gpd
import baltimore_landuse_code

county_pop = {
    3: 323655,
    5:  513941,
    13: 95423,
    25: 146580,
    27: 177327,
    35: 26988,
    510: 457735
}


col_list = ['agricultur', 'commercial', 'hight_resi', 'low_reside', 'medium_res', 'sparse_res']
col_str = ['agriculture', 'commercial', 'hight_residential', 'low_residential', 'medium_residential', 'sparse_residential']

def pop_weight(county, inFile='2010_TAZ/population_allocation.csv', gridPointFile='2010_TAZ/taz_lu_samples.shp'):
    weight = pd.read_csv(inFile)

    print(weight.head)
    print(weight.get_value(county, 'agricultur'))
    # gridPoint = gpd.read_file(gridPointFile)
    # gridPoint.COUNTYFP10 = gridPoint.COUNTYFP10.astype('int')
    # gridPoint = gridPoint[gridPoint.COUNTYFP10 == county]
    # #
    # #
    # gridPoint['lu_name'] = gridPoint.apply(lambda row: baltimore_landuse_code.CLASSIFICATION_STR[row.value], axis=1)
    # gridPoint['lu_code'] = gridPoint.apply(lambda row: baltimore_landuse_code.CLASSIFICATION[row.value], axis=1)
    # gridPoint['popWeight'] = gridPoint.apply(lambda row: baltimore_landuse_code.CLASSIFICATION[row.value], axis=1)
    # gridPoint = gridPoint.filter(items=['COUNTYFP10', 'TAZCE10', 'lu_code', 'geometry'])
    # #
    # # # print(gridPoint.head())
    # # print(len(gridPoint.index))
    # gridPoint = gridPoint[gridPoint.lu_code.isin(col_str)]
    # gridPoint.to_file('2010_TAZ_counties/population_' + str(county) + '.shp')
    # print(gridPoint.columns)

    # gridPoint = gridPoint[gridPoint[] = county] # TAZes in county
    # taz['num_hh'] = lu_samples.apply(lambda row: weight[taz.lu_code], axis=1)
    #
    # error = num_households[county] - df.value.sum() # Integer error should be added
    # # print(error, df.value.sum(), num_households[county])
    # taz = taz.sample(n=int(error))
    # df_incr.value = df_incr.value.apply(lambda x: x + 1)
    # df.update(df_incr)
    # df = df[df.value != 0]
    #
    # locations = pd.DataFrame()
    # hh_locations = []
    # # new_columns = ['location']
    # for index, row in df.iterrows():
    #     locations = [(row['geometry'].x, row['geometry'].y)] * int(row['value'])
    #     # print(locations, int(row['value']))
    #     hh_locations += locations
    # hh_locations = pd.DataFrame.from_records(hh_locations, columns=['x','y'])
    # hh_locations = hh_locations.sample(frac=1).reset_index(drop=True)
    # hh_locations.to_csv(outFile)
    # print(error, df.value.sum(), num_households[county])
pop_weight(3)
def clean_all_counties():
    for c in county_pop.keys():
        pop_weight(c)
# clean_all_counties()
