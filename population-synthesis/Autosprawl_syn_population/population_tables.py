################################################################################
# Description: Create population and household tables
################################################################################

import pandas as pd
import geopandas as gpd
import baltimore_landuse_code
import numpy as np

outFolder='to_db/'

DEGREE_PROJ = {'init': 'epsg:4326'}
CARTESIAN_PROJ = {'init': 'epsg:3857'}

inFolder = 'Baltimore_syn_population/'
counties = []

# code_county = {
#     24003 : 'AnneArundel', #24003
#     24510: 'BaltimoreCity', #24510
#     24005: 'BaltimoreCounty', #24005
#     24013: 'Carroll', #24013
#     24027: 'Howard', #24027
#     24035: 'QueenAnne', #24035
#     24025: 'Harford' #24025
# }
code_county = {
    24003 : '3', #24003
    24510: '510', #24510
    24005: '5', #24005
    24013: '13', #24013
    24027: '27', #24027
    24035: '35', #24035
    24025: '25' #24025
}

def prepare(inFolder='../Weighted_population/', outFile=outFolder+'pre_individual.csv'):
    HHID  = 1
    INDID = 1
    frames = []
    for countyCode, countyStr in code_county.items():
        # hhid,indid,APER,gender,age,educ,vehicles,income,school,employment
        fileName = inFolder + str(countyCode) + ".csv"
        df = pd.read_csv(fileName)
        df = df.sort_values(by=['indid'])
        print('-----county', countyCode)
        print(len(df.indid.unique()))
        print('hhid', len(df.hhid.unique()))
        mapINDID  = pd.Series(df.indid.unique()).to_frame(name='oldINDID')
        mapINDID['newINDID'] = mapINDID.index + INDID
        INDID += len(mapINDID.index)
        mapINDID.index = mapINDID.oldINDID

        mapHHID = pd.Series(df.hhid.unique()).to_frame(name='hhid')
        mapHHID['newHHID'] = mapHHID.index + HHID
        HHID += len(mapHHID.index)
        # mapHHID.index = mapHHID.hhid
        locations = pd.read_csv('population_by_county/' + countyStr + '.csv', squeeze=True, header=None)
        print('location size', locations.size)
        mapHHID['sla_address_id'] = locations
        mapHHID['sla_address_id'] = mapHHID['sla_address_id'].astype(int)

        df['indid'] = df.apply(lambda row: mapINDID.get_value(row.indid, 'newINDID'), axis=1)
        df = pd.merge(df,mapHHID, on='hhid')
        df.drop(['hhid'], axis=1, inplace=True)
        df.rename(columns={'newHHID':'hhid'}, inplace=True)

        frames.append(df)
    MetroPopulation = pd.concat(frames)
    MetroPopulation.to_csv(outFile, index=False)
prepare()

def test_individual(inFile='to_db/pre_individual.csv',outFile=outFolder+'individual.csv'):
    population = pd.read_csv(inFile)
    print('income ', population.income.value_counts())

# test_individual()

def income_category(amount):
    try:
        amount = int(amount)
    except:
        return 13
    if amount < 1000:
        return 1
    elif amount < 1500:
        return 2
    elif amount < 2000:
        return 3
    elif amount < 2500:
        return 4
    elif amount < 3000:
        return 5
    elif amount < 4000:
        return 6
    elif amount < 5000:
        return 7
    elif amount < 6000:
        return 8
    elif amount < 7000:
        return 9
    elif amount < 8000:
        return 10
    else:
        return 11


def format_individual(inFile='to_db/pre_individual.csv',outFile=outFolder+'individual.csv'):
    population = pd.read_csv(inFile) # 2769819 individual, hhid 1741649

    population.rename(columns={'indid': 'id',
                                'hhid': 'household_id',
                                'gender': 'gender_id',
                                'educ': 'education_id',
                                'age': 'age_category_id',
                                'vehicles':'vehicle_category_id',
                                # 'income':'income_id',
                                'APER':'household_size',
                                'employment': "employment_status_id"}, inplace=True)
                                # households
    print(population.columns)
    #  SCHOOL		School attendance
    # 0		N/A
    # 1		No, not in school
    # 2		Yes, in school
    # 9		Missing
    population["is_student"] = population.apply(lambda row: "FALSE" if row.school == 2 else "TRUE", axis=1)
    SCHOOL_MAP = {0:0, 1:1, 2:2, 3:3, 4:3, 5:3, 6:3, 7:4, 8:4, 9:5, 10:5, 11:6}
        # edu = [
        #     (0, 'N/A or not in school'),
        #     (1, 'Nursery school to grade 4'),
        #     (2, 'Grade 5, 6, 7, or 8'),
        #     (3, 'Grade 9, 10, 11, 12'),
        #     (4, 'College 1 or 2 years of college'),
        #     (5, 'College 3 or 4 years of college'),
        #     (6, 'College 5+ years of college')]
    population["education_id"] = population.apply(lambda row: SCHOOL_MAP[row.education_id] if row.school != 2  else 0, axis=1)
    # population["education_id"] = population.apply(lambda row: SCHOOL_MAP[row.education_id] if row.is_student else 0, axis=1)
    # population["income"] = 1 # TODO integrate
    # population["member_id"] = 2 # TODO
    population["income"] = population.apply(lambda row: income_category(row.income), axis=1)
    population["job_id"] = 0
    population["ethnicity_id"] = 0
    population["occupation_id"] = 0
    population["industry_id"] = 0
    population["transit_category_id"] = 0
    population["residential_status_id"] = 0
    population["taz_workedu_id"] = 0
    population["household_head"] = "FALSE"
    population["work_at_home"] = "FALSE"
    population["car_license"] = "FALSE"
    population["motor_license"] = "FALSE"
    population["vanbus_license"] = "FALSE"
    population["fixed_work_schedule"] = "FALSE"
    population["fixed_work_location"] = "FALSE"

    # population["postcode_id"] = 0
    # population["individual_type_id"] = 0
    # population["age_detailed_category"] = population["age"]
    # population["date_of_birth"] = "1/1/99"

    population.drop(['school'], axis=1, inplace=True)
    population = population[['id','household_id', 'ethnicity_id', 'employment_status_id', "gender_id", "education_id",
                            "occupation_id", "industry_id", "transit_category_id", "age_category_id", "residential_status_id",
                            "household_head", "income", "work_at_home", "car_license", "motor_license", "vanbus_license",
                            "is_student", "fixed_work_schedule", "fixed_work_location", "taz_workedu_id", "household_size",
                            "job_id", "vehicle_category_id"]]

    # population = population.reindex_axis(['id','household_id', 'ethnicity_id', 'employment_status_id', "gender_id", "education_id",
                            # "occupation_id", "industry_id", "transit_category_id", "age_category_id", "residential_status_id",
                            # "household_head", "income", "work_at_home", "car_license", "motor_license", "vanbus_license",
                            # "is_student", "fixed_work_schedule", "fixed_work_location", "taz_workedu_id", "household_size",
                            # "job_id", "vehicle_category_id"], axis=1)
    print(population.columns)
    print(len(population.columns))
    print('income ', population.income.value_counts())
    # print('income id', population.income_id.value_counts())
    population.to_csv('to_db/individual_with_income.csv', index=False)
format_individual()

def format_household(inFile='to_db/pre_individual.csv',outFile=outFolder+'household.csv'):
    population = pd.read_csv(inFile) # 2769819 individual, hhid 1741649 'vehicles':'vehicle_category_id',
    population =  population.filter(items=['hhid', 'age', 'APER', 'income', 'sla_address_id', 'vehicles'])
    population.rename(columns={'hhid': 'id', 'age' : 'age_category_id','APER':'household_size', 'vehicles':'vehicle_ownership_option_id'}, inplace=True) # 'vehicles':'vehicle_category_id',

    households  = population.drop_duplicates(subset=['id'])
    # age_group = population.groupby(['hhid', 'age_category_id'], as_index=False).size()
    age_group = population.filter(items=['id', 'age_category_id'])
    age_group = population.groupby(['id', 'age_category_id']).size().reset_index(name='count')
    age_under5 = age_group[age_group.age_category_id==0]
    age_under5['child_under5'] = age_under5['count']
    age_under15 = age_group[age_group.age_category_id<3]
    num_adults = age_group[age_group.age_category_id>4]

    age_under15 = age_under15.groupby(['id'])['count'].agg('sum').reset_index(name='child_under15')
    num_adults = num_adults.groupby(['id'])['count'].agg('sum').reset_index(name='num_adults')

    # df['total'].fillna(0, inplace=True)

    # print(age_group.head())
    # print(age_under15.head())
    # print(age_group.columns)

    households = pd.merge(households, num_adults, on=['id'], how='left')
    households = pd.merge(households, age_under15, on=['id'], how='left')
    households = pd.merge(households, age_under5, on=['id'], how='left')
    households['num_adults'].fillna(0, inplace=True)
    households['child_under15'].fillna(0, inplace=True)
    households['child_under5'].fillna(0, inplace=True)

    households['num_adults'] = households['num_adults'].astype(int)
    households['child_under15'] = households['child_under15'].astype(int)
    households['child_under5'] = households['child_under5'].astype(int)
    # print(households.head())
    households["workers"] = 0
    households["age_of_head"] = 0
    # households["taz_id"] = 0

    age_under15 = age_group[age_group.age_category_id<3]
    age_under15 = age_under15.groupby(['id'])['count'].agg('sum').reset_index(name='child_under15')
    #
    # population["lifestyle_id"] = 0
    # population["fm_unit_id] =
    # population["ethnicity_id"] = 0
    # population["vehicle_hitscategory_id"] = 0
    age_under15 = age_group[age_group.age_category_id<3]
    age_under15 = age_under15.groupby(['id'])['count'].agg('sum').reset_index(name='child_under15')

    hh_income = population.groupby(['id'])['income'].agg('sum').reset_index(name='hh_income')
    households = pd.merge(households, hh_income, on=['id'], how='left')
    households['hh_income'].fillna(0, inplace=True)
    # population["housing_duration"] =
    # population["pending_status_id"] =
    # population["pending_from_date"] =
    # population["unit_pending"] =
    # population["taxi_availability"] =
    # households["vehicle_ownership_option_id"] = 0
    households['fm_unit_id'] = 0
    # population["time_on_market"] =
    # population["time_off_market"] =
    # population["is_bidder"] =
    # population["is_seller"] =
    # population["buy_sell_interval"] =
    # population["move_in_date"] =
    # population["has_moved"] =
    # population["tenure_status"] =
    # population["awakened_day"] =
    # households = households.filter(items=[])
    # print(households.columns)
    # print(households.head())
    # LOCALIZE:::
    households = households[['id','household_size', 'child_under5', 'child_under15', 'num_adults', 'hh_income', 'workers', 'fm_unit_id', 'sla_address_id', 'vehicle_ownership_option_id']]

    households.to_csv(outFile, index=False)
    # print(households.head())
    # print(households.columns)
format_household()

def stats(inFile='to_db/pre_individual.csv', outFile='to_db/population_at_grid_point.csv'):
    individuals = pd.read_csv(inFile)
    individuals = individuals.filter(items=['employment', 'educ', 'sla_address_id', 'school'])
    individuals["is_student"] = individuals.apply(lambda row: int(row.school != 2), axis=1)
    individuals["working"] = individuals.apply(lambda row: int(row.employment == 1), axis=1)
    individuals["population"] = individuals.apply(lambda row: 1, axis=1)

    students = individuals.groupby(['sla_address_id'])['is_student'].agg('sum').reset_index(name='residential_students')
    workers = individuals.groupby(['sla_address_id'])['working'].agg('sum').reset_index(name='resident_workers')
    population = individuals.groupby(['sla_address_id'])['population'].agg('sum').reset_index(name='total_population')

    at_point = individuals.drop_duplicates(subset=['sla_address_id'])
    at_point = pd.merge(at_point, students, on='sla_address_id', how='left')
    at_point = pd.merge(at_point, workers, on='sla_address_id', how='left')
    at_point = pd.merge(at_point, population, on='sla_address_id', how='left')

    at_point = at_point[['sla_address_id','resident_workers','residential_students','total_population']]
    at_point.to_csv(outFile, index=False)
stats()
