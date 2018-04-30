import pandas as pd
import geopandas as gpd
import math
import numpy as np


samples = pd.read_csv('Processing_data/samples/samples_with_all_attributes.csv') # 52366, total weight: 187477.126042
total_population = pd.read_csv('Population_data/Baltimore_affs/ACS_15_5YR_B01003_with_ann.csv')
population_weights = 'Processing_data/multilevel_sample_weights/'
outFolder = 'Weighted_population/'

# Here hhid - household_id, indid - individual_id
def create_county_population(current_county, samples, total_population, weightFile):
    weights = pd.read_csv(weightFile)
    w_scaling = total / weights['weights'].sum()
    samples['weight'] = weights['weights'] * w_scaling

    ######################### Integerize households #########################
    unique_hh = samples.drop_duplicates('hhid', inplace=False)
    counts = samples['hhid'].value_counts()

    error_weight = 0
    num_in_population = {}
    syn_pop = 0

    SMALL_HHID = {}
    for index, row in unique_hh.iterrows():
        if error_weight > 0:
            int_num = math.floor(row.weight)
        else:
            int_num = math.ceil(row.weight)
        error_weight += (int_num - row.weight) * row.APER # ind weight
        syn_pop +=  int_num * row.APER
        num_in_population[row.hhid] = int_num
        SMALL_HHID[row.hhid] = index
    print('synthetic total population', syn_pop, ' number of households', sum(num_in_population.values())) # (unique_hh['weight']*unique_hh['APER']).sum())

    ####################### Write new population ############################
    max_num = max(num_in_population.values())
    scale = 10**(math.ceil(math.log(max_num, 10)))
    hhsample = 0

    new_population = []
    new_columns = ['hhid', 'indid', 'APER', 'gender' , 'age', 'educ', 'vehicles', 'income', 'school', 'employment']

    for index, sample in samples.iterrows():
        for i in range(num_in_population[sample.hhid]):
            # hhid = sample.hhid * scale + i # using old hhid
            hhid = SMALL_HHID[sample.hhid] * scale + i
            indid = hhid * 100 + (sample.indid % 100)
            new_population.append((int(hhid), int(indid),
                                    int(sample.APER), int(sample.gender),
                                    int(sample.age), int(sample.educ),
                                    int(sample.vehicles), int(sample.income_earn),
                                    int(sample.school), int(sample.employment)))

    synthetic_population = pd.DataFrame.from_records(new_population, columns=new_columns)
    synthetic_population.to_csv('synthesized_population.csv', index=False)

    ###################### Attribure statistics ########################################
    stats = {}
    stats['gender'] = synthetic_population['gender'].value_counts()
    stats['age'] = synthetic_population['age'].value_counts()
    stats['educ'] = synthetic_population['educ'].value_counts()
    stats['vehicles'] = synthetic_population['vehicles'].value_counts()
    stats['school'] = synthetic_population['school'].value_counts()
    stats['employment'] = synthetic_population['employment'].value_counts()
    stats['originalPop'] = total
    stats['syntheticPop'] = syn_pop
    # ###################### wrtie metadata  #############################################
    stats['gender'].to_csv(outFile + '_gender_stats.csv', index=True)
    stats['age'].to_csv(outFile + '_age_stats.csv', index=True)
    stats['educ'].to_csv(outFile + '_educ_stats.csv', index=True)
    stats['vehicles'].to_csv(outFile + '_vehicles_stats.csv', index=True)
    stats['school'].to_csv(outFile + '_school_stats.csv', index=True)
    stats['employment'].to_csv(outFile + '_employment_stats.csv', index=True)
    #
    se = pd.Series({'originalPop': total, 'syntheticPop':syn_pop})
    se.to_csv(outFile + '_pop_stats.csv', index=True)
    #
    # return stats


################ CREATE ALL COUNTIES' POPULATION #############################
for county in Baltimore_Metro_Counties:
    create_county_population(str(county), samples, total_population)
# create_county_population(str(24001), weights, samples, total_population)
