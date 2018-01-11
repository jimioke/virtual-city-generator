import pandas as pd

counties = [24001, 24003, 24005, 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
# counties = [24001, 24003, 24005] # 24009, 24011, 24013, 24015, 24017, 24019, 24021, 24023, 24025, 24027, 24029, 24031, 24033, 24035, 24037, 24039, 24041, 24043, 24045, 24047, 24510]
folder = 'Baltimore_syn_population2/'
outputFolder = 'Stats/'
vehicles_frames = []
for county in counties:
    current_county = str(county)
    header = ['category', current_county]
    vehicles = vehicles.drop_duplicates('hhid', inplace=True)
    vehicles = pd.read_csv(folder + current_county + '_vehicles_stats.csv', header=None)


    vehicles.columns = header
    vehicles.set_index('category', inplace=True)
    vehicles_frames.append(vehicles)


vehicles = pd.concat(vehicles_frames, axis=1)
vehicles.to_csv(outputFolder + 'agg_vehicles.csv', index=True)


#################### Write totals ####################################
vehicles.sum(axis=1).to_csv(outputFolder + 'Synthetic_sum_vehicles.csv', index=True)
