import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from fiona.crs import from_epsg

# To create
# Base-attributes.csv
# must have fields: shapeid, ID, NAME, NB_LANES, CAPACITY, SPEED, LENGTH, DIRECTION
# FNODE, TNODE, LinkCat,

# Base.csv
# fields: shapeid,ID,x,y,seq

# Points.csv
# fields: shapeid,x,y,nodeid,trafficLid
inputFolder = 'Santiago/from-OSMNET/'
outputFolder = 'Santiago/mainConversion-Input/'

def createBaseAttr():
    necessary_cols = ['name','lanes','maxspeed','from','to','highway','oneway','distance' ]
    edges = pd.read_csv(inputFolder + 'Santiago-Edges.csv', index_col=False, usecols=necessary_cols, low_memory=False)
    edges.rename(columns={'name': 'NAME', 'lanes': 'NB_LANES', 'maxspeed': 'SPEED', 'from': 'FNODE',
                'to': 'TNODE', 'highway': 'LinkCat', 'oneway': 'DIRECTION', 'distance': 'LENGTH'}, inplace=True)
    edges.index.name = 'shapeid'
    edges['ID'] = edges.index
    edges['ctps_ID'] = edges.index # TODO

    def set_direction(dir):
        if dir == 'yes':
            return -1 # two-way
        else:
            return 1
    def set_nb_lanes(nb_lanes):
        try:
            return min(int(nb_lanes), 7)
        except:
            return 2
    def set_LinkCat(LinkCat):
        return 'A'

    def set_SPEED(speed):
        try:
            return float(speed)
        except:
            return 60

    edges['LinkCat'] = edges['LinkCat'].apply(set_LinkCat)
    edges['SPEED'].fillna(60, inplace=True)
    edges['NAME'].fillna('No-name', inplace=True)
    edges['DIRECTION'] = edges['DIRECTION'].apply(set_direction)
    edges['NB_LANES'] = edges['NB_LANES'].apply(set_nb_lanes)
    edges['CAPACITY'] = edges['NB_LANES']*10
    edges.to_csv(outputFolder + 'Base-attributes.csv')

def createPoints():
    nodes = pd.read_csv(inputFolder + 'Santiago-Nodes.csv', index_col=False)
    nodes.index.name = 'shapeid'
    nodes['trafficLid'] = 0
    nodes.rename(columns={'id':'nodeid'}, inplace=True)
    nodes.to_csv(outputFolder + 'Points.csv')

def geometry(row):
    start = points.loc[row['fromnode']]
    end = points.loc[row['tonode']]
    # shorten edge
    x0 = start['x']
    y0 = start['y']
    x1 = end['x']
    y1 = end['y']
    vect_x = x1-x0
    vect_y = y1-y0
    return LineString([(x0 + vect_x*SHORT, y0 + vect_y*SHORT), (x1 - vect_x*SHORT, y1 - vect_y*SHORT)])
    # return MultiPoint([(start['x'], start['y']), (end['x'], end['y'])])

def createBase():
    # Edges --> 1 shapeid
    edges = pd.read_csv(outputFolder + 'Base-attributes.csv')
    points = pd.read_csv(inputFolder + 'Santiago-Nodes.csv', index_col='id')
    base_rows = []
    # shapeid, id, x, y, seq
    for index, row in edges.iterrows():
        row_id = row['ID']
        start = points.loc[row['FNODE']]
        end = points.loc[row['TNODE']]

        x0 = start['x']
        y0 = start['y']
        x1 = end['x']
        y1 = end['y']
        row1 = [ x0, y0, index, row_id, 1]
        row2 = [ x1, y1, index, row_id,  1]
        base_rows.extend([row1, row2])
    base = pd.DataFrame(base_rows, columns=[ 'x', 'y', 'shapeid', 'ID',  'seq'])
    base.to_csv(outputFolder + 'Base0.csv', index=False)


def createShortenedBase(shortOnOneSide=0.15):
    SHORT = shortOnOneSide
    # Edges --> 1 shapeid
    edges = pd.read_csv(outputFolder + 'Base-attributes.csv')
    points = pd.read_csv(inputFolder + 'Santiago-Nodes.csv', index_col='id')
    base_rows = []
    # shapeid, id, x, y, seq
    for index, row in edges.iterrows():
        row_id = row['ID']
        start = points.loc[row['FNODE']]
        end = points.loc[row['TNODE']]

        # shorten edge
        x0 = start['x']
        y0 = start['y']
        x1 = end['x']
        y1 = end['y']
        vect_x = x1-x0
        vect_y = y1-y0
        row1 = [ x0 + vect_x*SHORT, y0 + vect_y*SHORT, index, row_id, 1]
        row2 = [ x1 - vect_x*SHORT, y1 - vect_y*SHORT, index, row_id,  1]
        base_rows.extend([row1, row2])
    base = pd.DataFrame(base_rows, columns=[ 'x', 'y', 'shapeid', 'ID',  'seq'])
    base.to_csv(outputFolder + 'Base-shortened.csv', index=False)

def change_coordinate():
    oldCoord = 'epsg:4326'
    newCoord = 26986
    points = pd.read_csv(inputFolder + 'Santiago-Nodes.csv')
    geometry = [Point(xy) for xy in zip(points.x, points.y)]
    gdf = gpd.GeoDataFrame(points, crs={'init': oldCoord}, geometry=geometry)
    gdf['geometry'] = gdf['geometry'].to_crs(epsg=newCoord)
    gdf.crs = from_epsg(newCoord)
    gdf['x'] = gdf['geometry'].x
    gdf['y'] = gdf['geometry'].y
    gdf[['x', 'y', 'id']].to_csv(outputFolder + 'Base-diff-coord.csv', index=False)

change_coordinate()
# createBaseAttr()
# createShortenedBase()
