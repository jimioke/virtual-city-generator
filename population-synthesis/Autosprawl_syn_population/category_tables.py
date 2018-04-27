import pandas as pd
import csv
import re
import numpy as np
import math


# YEAR,DATANUM,SERIAL,HHWT,COUNTY,MET2013,CITYPOP,PUMA,CPUMA0010,GQ,OWNERSHP,OWNERSHPD,HHINCOME,PERNUM,PERWT,FAMSIZE,SEX,AGE,EDUC,EDUCD,EMPSTAT,EMPSTATD,LABFORCE,OCC,TRANWORK

# IPUMS (category checks)
# familysize 1->29
# sex (male-1, female 2)
# age (0-135)
# educ (0-11)


# ACS (category)
# age
# gender
# hhsize
# vehicles
################## AGE (IPUMS) to age (ACS) categories #####################
def age_category(outFile='to_db/age_category.csv'):
    age_category = ['Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 17 years', '18 and 19 years', '20 years', '21 years',
    '22 to 24 years', '25 to 29 years', '30 to 34 years', '35 to 39 years', '40 to 44 years', '45 to 49 years', '50 to 54 years',
    '55 to 59 years', '60 and 61 years', '62 to 64 years', '65 and 66 years', '67 to 69 years', '70 to 74 years', '75 to 79 years',
    '80 to 84 years', '85 years and over']

    ages = [ (i+1, age) for i, age in enumerate(age_category)]
    df = pd.DataFrame.from_records(ages, columns=['id', 'name'])
    df.to_csv(outFile, index=False)



def gender(outFile='to_db/gender.csv'):
    ################## SEX (IPUMS) to gender (ACS) categories #####################
    # IPUM sex (male-1, female 2) ACS {'0': ' Male', '1': ' Female'}
     ACS_gender = [(0, ' Male'), (1,' Female')]
     df = pd.DataFrame.from_records(ACS_gender)
     df.columns = ['id', 'name']
     df.to_csv(outFile, index=False)


################## vehicles per household #####################
# def mapVehicles(category):
#     if category == 0 or category==9:
#         return 0
#     elif category >= 4:
#         return 4
#     return category
#
# df_samples['vehicles'] = df['VEHICLES'].map(mapVehicles)

def education(outFile='to_db/education.csv'):
    #  SCHOOL		School attendance
    # 0		N/A
    # 1		No, not in school
    # 2		Yes, in school
    # 9		Missing
    edu = [
        (0, 'N/A or not in school'),
        (1, 'Nursery school to grade 4'),
        (2, 'Grade 5, 6, 7, or 8'),
        (3, 'Grade 9, 10, 11, 12'),
        (4, 'College 1 or 2 years of college'),
        (5, 'College 3 or 4 years of college'),
        (6, 'College 5+ years of college')]

        # edu = [ 'N/A or not in school',
        # 'Nursery school to grade 4',
        # 'Grade 5, 6, 7, or 8',
        # 'Grade 9, 10, 11, 12',
        # 'College 1 or 2 years of college',
        # 'College 3 or 4 years of college',
        # 'College 5+ years of college']
    df = pd.DataFrame.from_records(edu)
    df.columns = ['id', 'name']
    df.name = df.name.astype(str)
    df.to_csv(outFile, index=False)
     # {0:0, 1:1, 2:2, 3:3, 4:3, 5:3, 6:3, 7:4, 8:4, 9:5, 10:5, 11:6}

def employment_status(outFile='to_db/employment_status.csv'): #EMPSTAT
    status = [
        (0, 'N/A'),
        (1, 'Employed'),
        (2, 'Unemployed'),
        (3, 'Not in labor force')]
    df = pd.DataFrame.from_records(status)
    df.columns = ['id', 'name']
    df.to_csv(outFile, index=False)

def vehicles(outFile='to_db/vehicle_ownership_option_id.csv'):
    status = [
    (0,	'N/A'),
    (1,	'1 available'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6 (6+, 2000, ACS and PRCS)'),
    (7, '7+'),
    (9, 'No vehicles available')]
    df = pd.DataFrame.from_records(status)
    df.columns = ['id', 'description']
    df.to_csv(outFile, index=False)

age_category()
gender()
education()
employment_status()
vehicles()
