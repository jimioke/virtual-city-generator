import pandas as pd
import geopandas as gpd


DEGREE_PROJ = {'init': 'epsg:4326'}
CARTESIAN_PROJ = {'init': 'epsg:3857'}

inFolder = 'Baltimore_syn_population/'
counties = []

code_county = {
    24001 : 'AnneArundel', #24003
    # 24510: 'BaltimoreCity', #24510
    # 24005: 'BaltimoreCounty', #24005
    # 24013: 'Carroll', #24013
    # 24027: 'Howard', #24027
    # 24035: 'QueenAnne', #24035
    # 24025: 'Harford' #24025
}

    # Synthetic
    # 00		N/A or no schooling
    # 01		Nursery school to grade 4
    # 02		Grade 5, 6, 7, or 8
    # 03		Grade 9
    # 04		Grade 10
    # 05		Grade 11
    # 06		Grade 12
    # 07		1 year of college
    # 08		2 years of college
    # 09		3 years of college
    # 10		4 years of college
    # 11		5+ years of college


    # '0','Not in School'
    # '1','Preschool'
    # '2','Primary'
    # '3','Secondary'
    # '4','Post secondary (JC/CI/ITE)'
    # '5','Polytechnic'
    # '6','University'
    # '7','International school'
    # '8','Private school'
    # '9','Special school'
    # '10','Others'
    # '11','Missing'

    SCHOOL_MAP = {
    0: 0,
    1: 1,
    2: 3,
    3: 3,
    4: 3,
    5: 3,
    6: 3,
    7: 6,
    8: 6,
    9: 6,
    10: 6,
    11: 6,
    }

def prepare(inFolder=inFolder):
    MetroPopulation = []
    HHID  = 1
    INDID = 1
    for countyCode in code_county.keys():
        # hhid,indid,APER,gender,age,educ,vehicles,income,school,employment
        fileName = inFolder + str(countyCode) + ".csv"
        df = pd.read_csv(fileName)
        df = df.sort_values(by=['indid'])
        uniINDID  = df.indid.unique()
        uniHHID = df.hhid.unique()

        uniINDID['newID'] = uniINDID.index + INDID
        uniHHID['uniHHID'] = uniINDID.index + HHID
        INDID += len(uniINDID.index)
        HHID += len(uniHHID.index)
        df['indid'] = df.apply(lambda row: uniINDID.get_value(row.indid, 'newID'), axis=1)
        df['hhid'] = df.apply(lambda row: uniINDID.get_value(row.hhid, 'newID'), axis=1)

        location = gpd.read_file('.shp')
        geometry = [Point(xy) for xy in zip(location.x, location.y)]
        gdf = gpd.GeoDataFrame(df, crs=DEGREE_PROJ, geometry=geometry)
        MetroPopulation.append(gdf)

    MetroPopulation = gpd.GeoDataFrame( pd.concat( all_gdf, ignore_index=True) )
    MetroPopulation.crs = DEGREE_PROJ
    MetroPopulation.to_file(inFolder + 'all_counties.csv')

def prepareIndividual(inFile = inFolder+ 'all_counties.csv'):
    population = pd.read_csv(inFile)
    # hhid,indid,APER,gender,age,educ,vehicles,income,school,employment
    population.rename(columns={'indid': 'id',
                                'hhid': 'household_id'
                                'gender': 'gender_id',
                                'educ': 'education_id',
                                'age': 'age_category_id',
                                'vehicles':'vehicle_category_id',
                                'income':'income',
                                'APER':'size_household',
                                'school':
                                'employment': "employment_status_id"}, inplace=True)
                                # households

    population["education_id"] = population.apply(lambda row: SCHOOL_MAP[row.education_id], axis=1)
    population["student"] = population.apply(lambda row: "FALSE" if SCHOOL_MAP[row.education_id] == 0 else "TRUE", axis=1)

    population["date_of_birth"] = "1/1/99"
    population["income"] = 1 # to integrate
    population["member_id"] = 2 # TODO
    population["job_id"] = 0
    population["individual_type_id"] = 0
    population["ethnicity_id"] = 0
    population["occupation_id"] = 0
    population["industry_id"] = 0
    population["transit_category_id"] = 1
    population["residential_status_id"] = 1
    population["household_head"] = "FALSE"
    population["work_at_home"] = "FALSE"
    population["car_license"] = "FALSE"
    population["motor_license"] = "FALSE"
    population["vanbus_license"] = "FALSE"
    population["age_detailed_category"] = population["age"]
    population["fixed_work_schedule"] = "FALSE"
    population["fixed_work_location"] = "FALSE"
    population["taz_workedu_id"] = "FALSE"
    population["postcode_id"] = 0
    population.to_csv(inFolder + 'individual.csv')

def prepareHH(inFile = inFolder+ 'all_counties.csv'):
    population = pd.read_csv(inFile)
    # hhid,indid,APER,gender,age,educ,vehicles,income,school,employment
    population.rename(columns={'indid': 'id',
                                'hhid': 'id'
                                'gender': 'gender_id',
                                'educ': 'education_id',
                                'age': 'age_category_id',
                                'vehicles':'vehicle_category_id',
                                'income':'income',
                                'APER':'hh_size',
                                'school':
                                'employment': "employment_status_id"}, inplace=True)
                                # households

    population["education_id"] = population.apply(lambda row: SCHOOL_MAP[row.education_id], axis=1)
    population["student"] = population.apply(lambda row: "FALSE" if SCHOOL_MAP[row.education_id] == 0 else "TRUE", axis=1)

    population["id"] =
    population["child_under4"] =
    population["child_under15"] =
    population["num_adults"] =
    population["workers"] =
    population["age_of_head"] = 0
    population["taz_id"] = 0

    population["lifestyle_id"] = 0
    population["fm_unit_id] =
    population["ethnicity_id"] = 0
    population["vehicle_hitscategory_id"] = 0
    population["hh_income"] =
    population["housing_duration"] =
    population["pending_status_id"] =
    population["pending_from_date"] =
    population["unit_pending"] =
    population["taxi_availability"] =
    population["vehicle_ownership_option_id"] =
    population["time_on_market"] =
    population["time_off_market"] =
    population["is_bidder"] =
    population["is_seller"] =
    population["buy_sell_interval"] =
    population["move_in_date"] =
    population["has_moved"] =
    population["tenure_status"] =
    population["awakened_day"] =





# id	individual	individual (person) id
# employment_status_id	individual	person type id (refer employment_status table in LT database for descriptions)
# gender_id	individual	gender of person
# education_id	individual	student type category id (refer education table in LT database descriptions)
# vehicle_category_id	individual	vehicle ownership type (refer vehicle_category table in LT database for descriptions)
# age_category_id	individual	age category id (refer age_category table in LT database for descriptions)
# income	individual	income of person
# work_at_home	individual	whether the person works from home
# car_license	individual	whether the person has licence to drive car
# motor_license	individual	whether the person has licence to drive motorcycle
# vanbus_license	individual	whether the person has licence to drive heavy vehicles
# time_restriction	job	whether the person has strict work hours
# fixed_workplace	job	whether the person has a fixed work location
# is_student	job	is the person a student
# sla_address_id	establishment	address of primary activity location (school location if student, work location if employed)
# id	household	id of household to which the person belongs
# sla_address_id	fm_unit_res	person's home address id
# size	household	size of person's household
# child_under4	household	number of household members under 4 years of age
# child_under15	household	number of household members under 15 years of age
# adult	household	number of adults in household
# workers	household	number of earning individuals in the household
