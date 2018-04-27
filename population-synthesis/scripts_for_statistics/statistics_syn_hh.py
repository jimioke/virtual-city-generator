import pandas as pd

counties = [24001, 24003, 24005, 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
# counties = [24001, 24003, 24005] # 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
folder = 'Baltimore_syn_population2/'
outputFolder = 'Stats/'
gender_frames = []
age_frames = []
educ_frames = []
pop_frames = []
vehicles_frames = []
for county in counties:
    current_county = str(county)
    header = ['category', current_county]
    gender = pd.read_csv(folder + current_county + '_gender_stats.csv', header=None)
    age = pd.read_csv(folder + current_county + '_age_stats.csv', header=None)
    educ = pd.read_csv(folder + current_county + '_educ_stats.csv', header=None)
    pop = pd.read_csv(folder + current_county + '_pop_stats.csv', header=None)
    vehicles = pd.read_csv(folder + current_county + '_vehicles_stats.csv', header=None)
    vehicles = vehicles.drop_duplicates()

    gender.columns = header
    age.columns = header
    educ.columns = header
    vehicles.columns = header

    gender.set_index('category', inplace=True)
    age.set_index('category', inplace=True)
    educ.set_index('category', inplace=True)
    vehicles.set_index('category', inplace=True)

    gender_frames.append(gender)
    age_frames.append(age)
    educ_frames.append(educ)
    pop_frames.append(pop)
    vehicles_frames.append(vehicles)

gender = pd.concat(gender_frames, axis=1)
age = pd.concat(age_frames, axis=1)
educ = pd.concat(educ_frames, axis=1)
vehicles = pd.concat(vehicles_frames, axis=1)

gender.to_csv(outputFolder + 'agg_gender.csv', index=True)
age.to_csv(outputFolder + 'agg_age.csv', index=True)
educ.to_csv(outputFolder + 'agg_educ.csv', index=True)
vehicles.to_csv(outputFolder + 'agg_vehicles.csv', index=True)


#################### Write totals ####################################
gender.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_gender.csv', index=True)
age.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_age.csv', index=True)
gender.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_gender.csv', index=True)
educ.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_educ.csv', index=True)
vehicles.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_vehicles.csv', index=True)
