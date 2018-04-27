import pandas as pd
import geopandas as gpd
import math
import numpy as np


Baltimore_Metro_Counties = [24003, 24510, 24005, 24013, 24027, 24035, 24025]

synthetic_population = 'Baltimore_syn_population_with_location/'
locations_for_households = '5-shuffled_location_for_households/locations_'
outFolder = 'Baltimore_syn_population_with_location/localized/'

def localize_county(current_county):
    syn_population =  pd.read_csv(synthetic_population + current_county + '.csv')
    shuffled_locations = pd.read_csv(locations_for_households + current_county + '.csv')
    households = syn_population.hhid.unique()
    assert (len(households) == len(shuffled_locations))
    x_location = shuffled_locations['x'].tolist()
    y_location = shuffled_locations['y'].tolist()
    hh_to_location_x = dict(zip(households, x_location))
    hh_to_location_y = dict(zip(households, y_location))

    syn_population['x'] = syn_population['hhid'].apply(lambda hhid: hh_to_location_x[hhid])
    syn_population['y'] = syn_population['hhid'].apply(lambda hhid: hh_to_location_y[hhid])
    # ['hhid', 'indid', 'APER', 'gender' , 'age', 'educ', 'vehicles', 'x', 'y']
    syn_population[['hhid', 'indid']] = syn_population[['hhid', 'indid']].applymap(np.int64)
    syn_population.to_csv(outFolder + current_county + '.csv')

################ CREATE ALL COUNTIES' POPULATION #############################
for county in Baltimore_Metro_Counties:
    localize_county(str(county))
# create_county_population(str(24001), weights, samples, total_population)
