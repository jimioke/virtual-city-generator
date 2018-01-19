import geopandas as gpd
import pandas as pd
import numpy as np
from random import sample
import numpy as np

inFolder = 'process-work/3-raster-point-weights/'
# outFolder = 'process/4-nonzero-point-weights/point_weights_'
outFolder = 'process-work/5-work-locations/locations_'
# pop_weight = 'raster_points/raster_points.shp'
# nonzero_points =  'landuse_popweight/nonzero_point_weights.shp'

# counties = {
# 'AnneArundel': '24003',  # resulted 64095
# 'BaltimoreCity': '24510', # 151146
# 'BaltimoreCounty': '24005',
# 'Carroll': '24013',
# 'Howard' : '24027',
# 'QueenAnne' : '24035',
# 'Harford' : '24025'
# }

#  EMPSTAT		Employment status [general version]
# 0		N/A
# 1		Employed
# 2		Unemployed
# 3		Not in labor force

# Synthetic household population size
num_workers_counties = {
    '24003': 371263,
    '24510': 356124,
    '24005': 528526,
    '24013': 111807,
    '24027': 207195,
    '24035': 31488,
    '24025': 164934,
}

def update_vals(row, update_index):
    if row.index in update_index:
        row.value += 1
    return row

for countyCode, num_workers in num_workers_counties.items():
    fileName = inFolder + countyCode + '.shp'
    outFile = outFolder + countyCode + '.csv'
    df = gpd.read_file(fileName) # Baltimore 1235000 points
    df = df[df.value != 0]
    scale = num_workers / df.value.sum()
    df.value = (df.value * scale).apply(np.floor)
    error = num_workers - df.value.sum() # Integer error should be added
    # print(error, df.value.sum(), num_households[county])
    df_incr = df.sample(n=int(error))
    df_incr.value = df_incr.value.apply(lambda x: x + 1)
    df.update(df_incr)
    df = df[df.value != 0]

    school_locations = []
    # new_columns = ['location']
    for index, row in df.iterrows():
        locations = [(row['geometry'].x, row['geometry'].y)] * int(row['value'])
        # print(locations, int(row['value']))
        school_locations += locations
    locations = pd.DataFrame.from_records(school_locations, columns=['x','y'])
    # Shuffle locations
    locations = locations.sample(frac=1).reset_index(drop=True)
    locations.to_csv(outFile)
    print(error, len(df.value.sum()), len(locations), num_workers)

# County, number of rasters
# 24003 64095
# 24510 151146
# 24005 54820
# 24013 39679
# 24027 40968
# 24035 7351
# 24025 39768
