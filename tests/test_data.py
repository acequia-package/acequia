

import pytest
from pandas import DataFrame
from geopandas import GeoDataFrame
from acequia.data import knmi_raingauches, knmi_weatherstations

def test_knmi_raingauches():
    
    df = knmi_raingauches(geo=False)
    assert isinstance(df, DataFrame)
    assert not df.empty

    df = knmi_raingauches(geo=True)
    assert isinstance(df, GeoDataFrame)
    assert not df.empty


def test_knmi_weatherstations():
    
    df = knmi_weatherstations(geo=False)
    assert isinstance(df, DataFrame)
    assert not df.empty

    df = knmi_weatherstations(geo=True)
    assert isinstance(df, GeoDataFrame)
    assert not df.empty
