import pandas as pd

counties = [24001, 24003, 24005, 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
# counties = [24001, 24003, 24005] # 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
folder = 'Outputs/'
outputFolder = 'Stats/'
gender_frames = []
age_frames = []
educ_frames = []
pop_frames = []
vehicles_frames = []
for county in counties:
    current_county = str(county)
    header = ['category', current_county]
    gender = pd.read_csv(folder + current_county + '_gender.dat', delim_whitespace=True)
    age = pd.read_csv(folder + current_county + '_age.dat', delim_whitespace=True)
    vehicles = pd.read_csv(folder + current_county + '_vehicles.dat', delim_whitespace=True)

    gender.columns = header
    age.columns = header
    vehicles.columns = header

    gender.set_index('category', inplace=True)
    age.set_index('category', inplace=True)
    vehicles.set_index('category', inplace=True)

    gender_frames.append(gender)
    age_frames.append(age)
    vehicles_frames.append(vehicles)

gender = pd.concat(gender_frames, axis=1)
age = pd.concat(age_frames, axis=1)
vehicles = pd.concat(vehicles_frames, axis=1)

gender.to_csv(outputFolder + 'Original_agg_gender.csv', index=True)
age.to_csv(outputFolder + 'Original_agg_age.csv', index=True)
vehicles.to_csv(outputFolder + 'Original_agg_veh.csv', index=True)


#################### Write totals ####################################
gender.sum(axis=1).to_csv(outputFolder + 'Original_sum_gender.csv', index=True)
age.sum(axis=1).to_csv(outputFolder + 'Original_sum_age.csv', index=True)
vehicles.sum(axis=1).to_csv(outputFolder + 'Original_sum_vehicles.csv', index=True)
