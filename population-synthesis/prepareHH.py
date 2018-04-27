################################################################################
# Description: Compute marginal totals for each SAL. Input formats might differ
#              but output files must have category and 'N' count columns.
#              For example:  gender N
#                            0 203336
#                            1 49555
################################################################################

import pandas as pd
import csv
import re

folder = 'Baltimore_affs/ACS_15_5YR_'
end = '_with_ann.csv'

sex_age = folder + 'B01001' + end
sex_education = folder + 'B15002' + end
unweighted_sample_population_count = folder + 'B00001' + end
unweighted_sample_housing = folder + 'B00001' + end
total_population = folder + 'B01003' + end
hhsize_vehicles = folder + 'B08201' + end
hhtypes = folder + 'B09019' + end

# Sex, age, education, size, vehicles
outputFolder = 'Outputs/'
gender_marg = outputFolder + 'GENDER.csv'
age_marg = outputFolder + 'AGE.csv'
edu_marg = outputFolder + 'EDU.dat'
veh_marg = outputFolder + 'VEHICLES.dat'

# sex_education = folder + 'ACS_15_5YR_B15002_SEX_BY_EDUCATIONAL.csv'
# hhtype_size = folder + 'ACS_15_5YR_B11016_HOUSEHOLD TYPE BY HOUSEHOLD SIZE.csv'
# hhincome = folder + 'ACS_15_5YR_B19001_HOUSEHOLD INCOME.csv'
# df = pd.read_csv(sex_age_file, skiprows=1)
# df = pd.read_csv(sex_education, skiprows=1)
# df = pd.read_csv(hhtype_size, skiprows=1)
# print("a_b".split("_")[1])
# df = df.select(lambda x: not re.search('Margin of Error', x), axis=1)

def cleanHeader(x):
    attrs  = x.split(';')
    if len(attrs) == 2:
        return attrs[1]
    return x

def firstAttr(x):
    attrs  = x.split(':')
    if len(attrs) == 2:
        return attrs[0]
    return x

def secondAttr(x):
    attrs  = x.split(':')
    if len(attrs) == 2:
        return attrs[1]
    return x

def code_category(df, orderColumn):
    attr_category = {}
    attr_category_code = []
    new_columns = []
    for i in range(len(orderColumn)):
        attr_category[str(i)] = orderColumn[i]
        new_columns.append(str(i))
    df.columns = new_columns # df.rename(columns = {orderColumn[i]:str(i)})
    return attr_category

def writeCountyFiles(df, attribute, outFolder):
    for index, county in df.iterrows():
        filePref = outFolder + str(index) +"_" + attribute + ".dat"
        f = open(filePref, 'w')
        f.write(attribute +' N\n')
        for i in range(len(df.columns)):
            f.write(str(df.columns[i]) + ' ' + str(county[i]) +'\n')
        f.close()

def compute_marginals(marginal2dFile):
    df = pd.read_csv(marginal2dFile, skiprows=1)
    df.set_index('Id2', inplace=True) # County
    # Clean table
    if 'Estimate; Total:' in df.columns:
        df = df.drop(['Estimate; Total:'], axis=1)
    # print(df.columns)
    df = df.filter(regex='Estimate;.*')
    df.rename(columns=cleanHeader, inplace=True)

    # Gender marginals
    original_column = df.columns
    df.rename(columns=firstAttr, inplace=True)
    df_attr1 = df.groupby(df.columns, axis=1).sum()

    # Age marginals
    df.columns = original_column
    df.rename(columns=secondAttr, inplace=True)
    df_attr2 = df.groupby(df.columns, axis=1).sum()

    # Clean totals (leftover)
    if '' in df_attr1.columns:
        df_attr1 = df_attr1.drop([''], axis=1)

    if '' in df_attr2.columns:
        df_attr2 = df_attr2.drop([''], axis=1)

    return df_attr1, df_attr2

def compute_marginals_using_columns(marginal2dFile, columns):
    df = pd.read_csv(marginal2dFile, skiprows=1)
    df.set_index('Id2', inplace=True) # County
    df_totals = pd.DataFrame(index=df.index)
    for column in columns:
        df_totals[column] = df.filter(regex='^.*' + column + '.*$')
    return df_totals

############################ WRITE 1D marginals for each county ################
age_column = [' - Under 5 years', ' - 5 to 9 years', ' - 10 to 14 years', ' - 15 to 17 years', ' - 18 and 19 years', ' - 20 years', ' - 21 years',
' - 22 to 24 years', ' - 25 to 29 years', ' - 30 to 34 years', ' - 35 to 39 years', ' - 40 to 44 years', ' - 45 to 49 years', ' - 50 to 54 years',
' - 55 to 59 years', ' - 60 and 61 years', ' - 62 to 64 years', ' - 65 and 66 years', ' - 67 to 69 years', ' - 70 to 74 years', ' - 75 to 79 years',
' - 80 to 84 years', ' - 85 years and over']

vehicle_column = [' - No vehicle available', ' - 1 vehicle available', ' - 2 vehicles available', ' - 3 vehicles available', ' - 4 or more vehicles available']
vehicle_column = ['Estimate; Total:' + t for t in  vehicle_columns]
gender_column = [' Male', ' Female']

df_gender, df_age = compute_marginals(sex_age)
category_gender = code_category(df_gender, gender_column)
writeCountyFiles(df_gender, 'gender', outputFolder)

category_age = code_category(df_age, age_column)
writeCountyFiles(df_age, 'age', outputFolder)

df_vehicles = compute_marginals_using_columns(hhsize_vehicles, vehicle_column)
categore_vehicle = code_category(df_vehicles, df_vehicles.columns)
writeCountyFiles(df_vehicles, 'vehicles', outputFolder)

# print('\n\nhhsize', category_hhsize)
# print('\n\nvehicles', categore_vehicle.values())
# print('\n\ngender', category_gender,)
# print('\n\nage', category_age)
