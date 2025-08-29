

import pytest
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

from acequia import GwSeries
from acequia import GwTimeStats
#import acequia as aq

dnpath = r'.\data\dinogws\B29A0850002_1.csv'

@pytest.fixture
def heads():
    gw = GwSeries.from_dinogws(dnpath)
    heads = gw.heads(ref='datum').resample('D').mean().dropna()
    return heads
    
@pytest.fixture
def headsmv():
    gw = GwSeries.from_dinogws(dnpath)
    heads = gw.heads(ref='surface').resample('D').mean().dropna()
    return heads

@pytest.fixture
def tmin():
    return '2000-01-01'

@pytest.fixture
def tmax():   
    return '2006-01-01'

def test_init(heads):

    # without time series
    gwstats = GwTimeStats()
    assert len(gwstats)==0
    assert isinstance(str(gwstats), str)
    assert gwstats.empty
    
    # with time series
    gwstats = GwTimeStats(heads)
    assert len(gwstats)!=0
    assert isinstance(str(gwstats), str)
    assert not gwstats.empty

def test_timestats(heads, tmin, tmax):
    
    # without time series
    gwstats = GwTimeStats()
    sr = gwstats.timestats()
    assert isinstance(sr, Series)
    assert not sr.empty

    # with time series
    gwstats = GwTimeStats(heads)
    sr = gwstats.timestats()
    assert isinstance(sr, Series)
    assert not sr.empty

    # with slice
    gwstats = GwTimeStats(heads)
    sr = gwstats.timestats(tmin=tmin, tmax=tmax)
    assert isinstance(sr, Series)
    assert not sr.empty
