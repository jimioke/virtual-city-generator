import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

inFolder = 'schools/'
outFolder = 'school_locations/'

high_edu = [
'Higher_Education_Private_Four_Year',
'Higher_Education_Private_Two_Year',
'Higher_Education_Public_Four_Year',
'Higher_Education_Public_Two_Year',
]

k_thru_12 = [
'K_thru_12_Education_Charter_Schools',
'K_thru_12_Education_Public_Schools',
]

counties = {
    'AnneArundel': 'Anne_2010LULC', #24003
    'BaltimoreCity': 'Baci_2010LULC', #24510
    'BaltimoreCounty': 'Baco_2010LULC', #24005
    'Carroll': 'Carr_2010LULC', #24013
    'Howard' : 'Howa_2010LULC', #24027
    'QueenAnne' : 'Quee_2010LULC', #24035
    'Harford' : 'Harf_2010LULC' #24025
}

counties = ['Baltimore City','Baltimore', 'Anne Arundel', 'Howard', 'Carroll', "Queen Anne's", 'Harford']

def get_k_thru_12():
    charter = pd.read_csv(inFolder + 'K_thru_12_Education_Charter_Schools.csv', usecols=['X', 'Y', 'county'])
    public = pd.read_csv(inFolder + 'K_thru_12_Education_Public_Schools.csv', usecols=['X', 'Y', 'County'])
    public.rename(columns={"County": "county"}, inplace=True)
    df = pd.concat([charter, public])
    df = df.loc[df['county'].isin(counties)]
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    df = df.drop(['X', 'Y'], axis=1)
    crs = {'init': 'epsg:4326'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf.to_file(outFolder+'k_thru_12_all')
    print("k_thru_12")
    print(gdf.groupby(['county']).size())

def get_higher_edu():
    # columns: ['X', 'Y', 'OBJECTID', 'sitename', 'sitedesc', 'streetaddr',
    # 'building_s', 'city', 'county', 'state', 'zip', 'phonenumbe', 'tollfree_n',
    # 'website', 'latitude', 'longitude', 'enrollment', 'grades_deg']
    all_edu = []
    for school in high_edu:
        df = pd.read_csv(inFolder + school + '.csv', usecols=['X', 'Y', 'county', 'enrollment'])
        all_edu.append(df)
    df = pd.concat(all_edu)
    df = df.loc[df['county'].isin(counties)]
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    df = df.drop(['X', 'Y'], axis=1)
    crs = {'init': 'epsg:4326'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf.to_file(outFolder+'high_edu_all')
    print("higher edu")
    print(gdf.groupby(['county']).size())

get_k_thru_12()
get_higher_edu()
