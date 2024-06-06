
import pytest
##import collections
##import numpy as np
from pandas import DataFrame
import pandas as pd
from geopandas import GeoDataFrame

from acequia import GwCollection, GwFiles, WaterWeb, GwSeries, HydroMonitor, BroGwCollection
import acequia as aq

dinodir = '.\\data\\dinogws_small\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'
wwfile = '.\\data\waterweb\\waterweb_csv_kolommen.csv' #Dwingelderveld.csv'
hmfile = r'.\\data\\hymon\\hydromonitor_testdata.csv'

@pytest.fixture
def gwc_dino():
    # test_from_dinocsv()
    gwc = GwCollection.from_dinocsv(dinodir)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, GwFiles)
    return gwc

@pytest.fixture
def gwc_json(gwc_dino):

    # write json files
    for gw in gwc_dino.iteritems():
        gw.to_json(f'{jsondir}{gw.name()}.json')

    # test_from_json()
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

@pytest.fixture
def gwc_brodownload():
    # test_from_brodownload()
    gwc = aq.GwCollection.from_brodownload(
        xmin = 259500,
        xmax = 259650,
        ymin = 489950,
        ymax = 490100,
        title = 'Agelerbroek',
        )
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, BroGwCollection)
    return gwc

# Test basic methods
# ------------------

# test len
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_ww, gwc_hm, gwc_brodownload])
def test_len(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    assert len(gwc)!=0

# test repr
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_ww, gwc_hm, gwc_brodownload])
def test_repr(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    assert isinstance(repr(gwc),str)

# test property names
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_ww, gwc_hm, gwc_brodownload])
def test_names(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    assert isinstance(gwc.names, list)
    assert gwc.names # assert list is not empty

# test iteritems
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_ww, gwc_hm, gwc_brodownload])
def test_iteritems(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    for gw in gwc.iteritems():
        assert isinstance(gw, GwSeries)

# test get_gwseries
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_ww, gwc_hm, gwc_brodownload])
def test_get_gwseries(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    gwname = gwc.names[0]
    gw = gwc.get_gwseries(gwname)
    assert isinstance(gw, GwSeries)


# Test advanced statistics
# ------------------------

# test tube_stats
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_brodownload])
def test_tubestats(gwc, request): 
    gwc = request.getfixturevalue(gwc.__name__)
    df = gwc.get_tubestats(ref='datum')
    assert isinstance(df, DataFrame)
    assert not df.empty

# test ecostats
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_brodownload]) #, gwc_ww, gwc_hm])
def test_ecostats(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    df = gwc.get_ecostats(ref='datum', units='days', step=5)
    assert isinstance(df, DataFrame)
    assert not df.empty

# test get_gxg
@pytest.mark.parametrize('gwc', [gwc_dino, gwc_json, gwc_brodownload])
def test_get_gxg(gwc, request):
    gwc = request.getfixturevalue(gwc.__name__)
    df = gwc.get_gxg(ref='datum')
    assert isinstance(df, DataFrame)
    assert not df.empty

