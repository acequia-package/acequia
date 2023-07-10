
import pytest
##import collections
##import numpy as np
from pandas import DataFrame
import pandas as pd
from geopandas import GeoDataFrame


from acequia import GwCollection, GwFiles, WaterWeb, GwSeries, HydroMonitor
import acequia as aq

dinodir = '.\\data\\dinogws_small\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'
wwfile = '.\\data\waterweb\\grolloer koelanden.csv'
hmfile = r'.\\data\\hymon\\hydromonitor_testdata.csv'

@pytest.fixture
def gwc():
    # test_from_dinocsv()
    gwc = GwCollection.from_dinocsv(dinodir)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, GwFiles)
    return gwc

@pytest.fixture
def gwc_json():
    # test_from_dinocsv()
    gwc = GwCollection.from_json(jsondir)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, GwFiles)
    return gwc

@pytest.fixture
def gwc_ww():
    # test_from_waterweb()
    gwc = GwCollection.from_waterweb(wwfile)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, WaterWeb)
    return gwc

@pytest.fixture
def gwc_hm():
    # test_from_hydromonitor()
    gwc = GwCollection.from_hydromonitor(hmfile)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, HydroMonitor)
    return gwc


def test_len(gwc):
    assert len(gwc)!=0

def test_repr(gwc):
    assert isinstance(repr(gwc),str)

def test_ecostats(gwc):
    df = gwc.get_ecostats(ref='datum', units='days', step=5)
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_headstats(gwc): 
    df = gwc.get_headstats(ref='datum')
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_get_xg(gwc):
    df = gwc.get_xg(ref='datum')
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_timestats(gwc):
    gdf = gwc.get_timestats(ref='datum', asgeo=True)
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

def test_iteritems(gwc, gwc_json, gwc_ww, gwc_hm):
    for gw in gwc.iteritems():
        assert isinstance(gw, GwSeries)

    for gw in gwc_json.iteritems():
        assert isinstance(gw, GwSeries)

    for gw in gwc_ww.iteritems():
        assert isinstance(gw, GwSeries)

    for gw in gwc_hm.iteritems():
        assert isinstance(gw, GwSeries)
