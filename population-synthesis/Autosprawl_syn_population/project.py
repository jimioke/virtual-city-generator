from shapely.geometry import LineString, Point
from shapely.ops import transform
from functools import partial
import pyproj
import pandas as pd
import geopandas as gpd


LAT_LONG_PROJECTION = pyproj.Proj(init='EPSG:4326')
BALTIMORE_PROJECTION = pyproj.Proj(init='EPSG:6487')

LAT_LONG_CRS = {'init': 'epsg:4326'}
BALTIMORE_CRS = {'init': 'epsg:6487'}

project = partial(
    pyproj.transform,
    LAT_LONG_PROJECTION,
    BALTIMORE_PROJECTION)


def project_x_y(fileName, outFile):
    df = pd.read_csv(fileName)
    column_order = df.columns
    print(df.columns)
    df['geometry'] = df.apply(lambda row: Point(row.x_coord, row.y_coord),axis=1)
    gdf = gpd.GeoDataFrame(df, crs=LAT_LONG_CRS, geometry=df['geometry'])
    print(gdf.columns)
    gdf = gdf.to_crs(BALTIMORE_CRS)
    # gdf.to_file(outFOLDER + 'projected')

    gdf['x_coord'] = gdf.apply(lambda row: row.geometry.x,axis=1)
    gdf['y_coord'] = gdf.apply(lambda row: row.geometry.y,axis=1)

    df = gdf[column_order]
    df.to_csv(outFile, index=False)

project_x_y('to_db/sla_address_id_not_projected.csv', 'to_db/sla_address_id.csv')
