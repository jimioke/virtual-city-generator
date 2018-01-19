import geopandas as gpd
import pandas as pd
from sklearn.utils import shuffle
import numpy as np
from random import sample
import numpy as np

inFolder = 'process/3-raster-point-weights/point_weights_'
# outFolder = 'process/4-nonzero-point-weights/point_weights_'
outFolder = 'process/5-shuffled_locations_for_households/locations_'
pop_weight = 'raster_points/raster_points.shp'
nonzero_points =  'landuse_popweight/nonzero_point_weights.shp'

counties = {
'AnneArundel': '24003',  # resulted 64095
'BaltimoreCity': '24510', # 151146
'BaltimoreCounty': '24005',
'Carroll': '24013',
'Howard' : '24027',
'QueenAnne' : '24035',
'Harford' : '24025'
}

# Synthetic household population size
num_households = {
'AnneArundel': 323655,  # resulted 64095
'BaltimoreCity': 457735, # 151146
'BaltimoreCounty': 513941,
'Carroll': 95423,
'Howard' : 177327,
'QueenAnne' : 26988,
'Harford' : 146580
}

def update_vals(row, update_index):
    if row.index in update_index:
        row.value += 1
    return row

for county, countyCode in counties.items():
    fileName = inFolder + countyCode + '.shp'
    outFile = outFolder + countyCode + '.csv'
    df = gpd.read_file(fileName) # Baltimore 1235000 points
    df = df[df.value != 0]
    scale = num_households[county] / df.value.sum()
    df.value = (df.value * scale).apply(np.floor)
    error = num_households[county] - df.value.sum() # Integer error should be added
    # print(error, df.value.sum(), num_households[county])
    df_incr = df.sample(n=int(error))
    df_incr.value = df_incr.value.apply(lambda x: x + 1)
    df.update(df_incr)
    df = df[df.value != 0]

    locations = pd.DataFrame()
    hh_locations = []
    # new_columns = ['location']
    for index, row in df.iterrows():
        locations = [(row['geometry'].x, row['geometry'].y)] * int(row['value'])
        # print(locations, int(row['value']))
        hh_locations += locations
    hh_locations = pd.DataFrame.from_records(hh_locations, columns=['x','y'])
    hh_locations = hh_locations.sample(frac=1).reset_index(drop=True)
    hh_locations.to_csv(outFile)
    print(error, df.value.sum(), num_households[county])

# County, number of rasters
# 24003 64095
# 24510 151146
# 24005 54820
# 24013 39679
# 24027 40968
# 24035 7351
# 24025 39768
