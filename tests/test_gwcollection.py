
import pytest
##import collections
##import numpy as np
from pandas import DataFrame
import pandas as pd
from acequia import GwCollection, GwFiles, GwSeries
import acequia as aq

dinodir = '.\\data\\dinogws_small\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'

@pytest.fixture
def gwc():
    # test_from_dinocsv()
    gwc = GwCollection.from_dinocsv(dinodir)
    assert isinstance(gwc, GwCollection)
    assert isinstance(gwc._collection, GwFiles)

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

def test_iteritems(gwc):
    for gw in gwc.iteritems():
        assert isinstance(gw, GwSeries)