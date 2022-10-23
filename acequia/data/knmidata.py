"""
Datasets included with Acequia.
    
"""

import pkg_resources
import pandas as pd
import geopandas as gpd
from ..read.knmi_download import KnmiDownload

class KnmiData:
    """Retrieve Knmi standard data."""

    def __init__(self):
        pass

    def __repr__(self):
        return self.__class__.__name__

    @property
    def prc_stns(self):
        """Coordinates of KNMI precipitation stations."""

        # This is a stream-like object. If you want the actual info, call
        # stream.read()
        fpath = 'knmi_precipitation_coords.csv'
        stream = pkg_resources.resource_stream(__name__, fpath)
        prc =  pd.read_csv(stream, encoding='latin-1')
        prc['label'] = prc['stn_nr'].astype(str)+'_'+prc['stn_name']
        prc = prc.set_index('stn_nr')
        gdf = gpd.GeoDataFrame(
            prc, geometry=gpd.points_from_xy(prc.xcrd, prc.ycrd))
        gdf = gdf.set_crs('epsg:28992')
        return gdf

    @property
    def wtr_stns(self):
        """Knmi weather stations"""
        stn = KnmiDownload()
        wtr = stn.wtr_stns
        wtr['label'] = wtr.index.astype(str) + '_' + wtr['stn_name']
        gdf = gpd.GeoDataFrame(
            wtr, geometry=gpd.points_from_xy(wtr.lon, wtr.lat))
        gdf = gdf.set_crs('epsg:4326')
        gdf = gdf.to_crs('epsg:28992')
        return gdf

