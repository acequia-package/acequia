"""
Datasets included with Acequia.
    
"""

import pkg_resources
import pandas as pd
import geopandas as gpd
from ..read.knmi_download import KnmiDownload

def knmi_prc_coords():
    """Coordinates of KNMI precipitation stations."""

    # This is a stream-like object. If you want the actual info, call
    # stream.read()
    fpath = 'knmi_precipitation_coords.csv'
    stream = pkg_resources.resource_stream(__name__, fpath)
    prc =  pd.read_csv(stream, encoding='latin-1')
    prc = prc.set_index('stn_nr')
    gdf = gpd.GeoDataFrame(
        prc, geometry=gpd.points_from_xy(prc.xcrd, prc.ycrd))
    gdf = gdf.set_crs('epsg:28992')    
    return gdf

def knmi_wtr_stns():
    """Knmi weather stations"""
    stn = KnmiDownload()
    wtr = stn.wtr_stns
    gdf = gpd.GeoDataFrame(
        wtr, geometry=gpd.points_from_xy(wtr.lon, wtr.lat))
    gdf = gdf.set_crs('epsg:4326')
    gdf = gdf.to_crs('epsg:28992')
    return gdf

