
import pytest
from pandas import DataFrame
from geopandas import GeoDataFrame
import acequia as aq 

def test_data_wtr_stns():
    gdf = aq.data.knmi_data.knmi_wtr_stns()
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

def test_data_prc_stns():
    gdf = aq.data.knmi_data.knmi_prc_coords()
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

