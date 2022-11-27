
import pytest
from pandas import DataFrame
from geopandas import GeoDataFrame
from acequia import KnmiData


def test_data_wtr_stns():
    knmi = KnmiData()
    gdf = knmi.wtr_stns
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

def test_data_prc_stns():
    knmi = KnmiData()
    gdf = knmi.prc_stns
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

