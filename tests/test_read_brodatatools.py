

import pytest
import numpy as np
from pandas import Series, DataFrame
#import pandas as pd
from geopandas import GeoDataFrame
from acequia._read import brodatatools
from acequia import GwSeries
import acequia as aq
from brodata.gmw import GroundwaterMonitoringWell

@pytest.fixture
def gmwid():
    return 'GMW000000041041'

@pytest.fixture
def tube():
    return 1

@pytest.fixture
def bronhouderid():
    return '51048329'

@pytest.fixture
def gmwlist():
    return ['GMW000000011574', 'GMW000000011575', 'GMW000000011576']

@pytest.fixture
def extent():
    extent = [264600, 264700, 495800, 495900]
    return {'xmin':extent[0], 'xmax':extent[1], 'ymin':extent[2], 'ymax':extent[3]}

def test_get_bronhouder_gmwlist(bronhouderid):
    gmwids = brodatatools.get_bronhouder_gmwlist(bronhouderid)
    assert isinstance(gmwids, list)
    assert gmwids

def test_get_gmwprops(gmwid):
    sr = brodatatools.get_gmwprops('GMW000000041041')
    assert isinstance(sr, Series)
    assert not sr.empty

def test_get_gmwtubes(gmwid):
    tubes = brodatatools.get_gmwtubes(gmwid)
    assert isinstance(tubes, np.ndarray)
    assert tubes.all()

# this test takes a lot of time because the broserver 
# response is slow
def test_get_tubeobs(gmwid, tube):
    gw = brodatatools.get_tubeobs(gmwid, tube)
    assert isinstance(gw, GwSeries)

# this test takes a lot of time because the broserver 
# response is slow
def test_get_tubeobs_from_gmw(gmwid):
    gwserieslist = brodatatools.get_tubeobs_from_gmw(gmwid)
    assert isinstance(gwserieslist, list)
    assert all([isinstance(gw, GwSeries) for gw in gwserieslist])

def test_get_tubeobs_from_gmwlist(gmwlist):
    gwserieslist = brodatatools.get_tubeobs_from_gmwlist(gmwlist)
    assert isinstance(gwserieslist, list)
    assert all([isinstance(gw, GwSeries) for gw in gwserieslist])

def test_get_tubeobs_within_extent(extent): 
    gwserieslist = brodatatools.get_tubeobs_within_extent(
        xmin=extent['xmin'], xmax=extent['xmax'], ymin=extent['ymin'], 
        ymax=extent['ymax']
        )
    assert isinstance(gwserieslist, list)
    assert all([isinstance(gw, GwSeries) for gw in gwserieslist])

def test_get_tubeprops(gmwid, tube):
    sr = brodatatools.get_tubeprops(gmwid, tube)
    assert isinstance(sr, Series)
    assert not sr.empty

def test_gmw_exists(gmwid):
    assert brodatatools.gmw_exists(gmwid)
    assert not brodatatools.gmw_exists('999999999999')

# hidden methods with direct calls to brodata
# -------------------------------------------

def test_get_brodata_extent_gmwproperties(extent):
    df = brodatatools._get_brodata_extent_gmwproperties(
        xmin=extent['xmin'], xmax=extent['xmax'], ymin=extent['ymin'], 
        ymax=extent['ymax'])
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_get_brodata_extent_tubeproperties(extent):
    gdf = brodatatools._get_brodata_extent_tubeproperties(
        xmin=extent['xmin'], xmax=extent['xmax'], ymin=extent['ymin'], 
        ymax=extent['ymax'])
    assert isinstance(gdf, GeoDataFrame)
    assert not gdf.empty

def test_get_brodata_extent_observations(extent):
    gdf = brodatatools._get_brodata_extent_observations(
        xmin=extent['xmin'], xmax=extent['xmax'], ymin=extent['ymin'], 
        ymax=extent['ymax'])
    assert isinstance(gdf, GeoDataFrame)
    assert not gdf.empty

def test_get_brodata_gmw_tubeproperties(gmwid):
    df = brodatatools._get_brodata_gmw_tubeproperties(gmwid)
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_get_brodata_gmw(gmwid):
    res = brodatatools._get_brodata_gmw(gmwid)
    assert isinstance(res, GroundwaterMonitoringWell)

def test_get_brodata_tubeobservations(gmwid, tube):
    df = brodatatools._get_brodata_tubeobservations(gmwid, tube)
    assert isinstance(df, DataFrame)
    assert not df.empty
