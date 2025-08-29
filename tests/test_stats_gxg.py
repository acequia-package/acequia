

import pytest
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

from acequia import GwSeries
from acequia import GxgStats
from acequia._stats.utils import get_ts1428


@pytest.fixture
def gwseries():
    return GwSeries.from_json(r'.\data\json\BRO41484_1.json')

@pytest.fixture
def ts(gwseries):
    ts = gwseries.heads(ref='datum')
    ts = ts['2012-01-01':'2016-12-31'] # shorten for speed
    ts = ts.resample('D').mean().dropna()
    return ts

@pytest.fixture
def ts1428_hydroyear():
    # this time series is used for validity checks
    # don't change the series or the tests will break
    gw = GwSeries.from_json(r'.\data\json\BRO41484_1.json')
    ts = gw.heads(ref='datum')
    ts = ts.resample('D').mean().dropna()
    ts = get_ts1428(ts, maxlag=0, remove_outer_nans=False)
    ts = ts['2010-04-01':'2011-03-28'].copy()
    return ts


@pytest.fixture
def surface(gwseries):
    return gwseries.surface()

"""
@pytest.fixture
def tmin():
    return '1980-01-01'


@pytest.fixture
def tmax():   
    return '1986-01-01'
"""

def test_init(ts):

    # without time series
    stats = GxgStats()
    assert len(stats)==0
    assert isinstance(str(stats), str)
    assert stats.empty
    
    # with time series
    stats = GxgStats(ts)
    assert len(stats)!=0
    assert isinstance(str(stats), str)
    assert not stats.empty


def test_is_1428hydroyear(ts1428_hydroyear):
    stats = GxgStats()
    assert stats.is_ts1428hydroyear(ts1428_hydroyear)


def test_is_valid_ts1428hydroyear(ts1428_hydroyear):
    stats = GxgStats()
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='strict')
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='moderate', purpose='GHG')
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='moderate', purpose='GLG')
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='generous', purpose='GHG')
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='generous', purpose='GLG')
    assert stats.is_valid_ts1428hydroyear(ts1428_hydroyear, validation='naive')


def test_ts1428hydroyear_hg3_values(ts1428_hydroyear):
    stats = GxgStats()
    sr = stats._ts1428hydroyear_hg3_values(ts1428_hydroyear)
    assert isinstance(sr, Series)
    assert len(sr)==3


def test_ts1428hydroyear_lg3_values(ts1428_hydroyear):
    stats = GxgStats()
    sr = stats._ts1428hydroyear_lg3_values(ts1428_hydroyear)
    assert isinstance(sr, Series)
    assert len(sr)==3


def test_hg3_table(ts):
    stats = GxgStats(ts)
    for validation in ['strict', 'moderate', 'generous', 'naive']:
        df = stats.hg3_table(validation=validation)
        assert isinstance(df, DataFrame)
        assert not df.empty


def test_lg3_table(ts):
    stats = GxgStats(ts)
    for validation in ['strict', 'moderate', 'generous', 'naive']:
        df = stats.lg3_table(validation=validation)
        assert isinstance(df, DataFrame)
        assert not df.empty


def test_hg3(ts):

    stats = GxgStats(ts)
    for validation in ['strict', 'moderate', 'generous', 'naive']:
        sr = stats.hg3(validation=validation)
        assert isinstance(sr, Series)
        assert not sr.empty

def test_lg3(ts):

    stats = GxgStats(ts)
    for validation in ['strict', 'moderate', 'generous', 'naive']:
        sr = stats.lg3(validation=validation)
        assert isinstance(sr, Series)
        assert not sr.empty


def test_vg1(ts):

    # with series
    stats = GxgStats(ts)
    for refdate in stats.VGDATES:
        sr = stats.vg1(refdate=refdate, maxlag=1)
        assert isinstance(sr, Series)
        assert not sr.empty

    # without series
    stats = GxgStats()
    sr = stats.vg1()
    assert isinstance(sr, Series)
    assert sr.empty


def test_vg3(ts):

    # with series
    stats = GxgStats(ts)
    sr = stats.vg3()
    assert isinstance(sr, Series)
    assert not sr.empty

    # without series
    stats = GxgStats()
    sr = stats.vg3()
    assert isinstance(sr, Series)
    assert sr.empty


def test_calculate_xg_nap(ts):

    # with time series
    stats = GxgStats(ts)
    res = stats._calculate_xg_nap(validation='moderate', maxlag=7)
    assert isinstance(res, DataFrame)
    assert not res.empty

    # without time series
    stats = GxgStats()
    res = stats._calculate_xg_nap()
    assert isinstance(res, DataFrame)
    assert res.empty


def test_xg(ts, surface):

    # relative to datum
    stats = GxgStats(ts)
    res = stats.xg(reference='datum')
    assert isinstance(res, DataFrame)
    assert not res.empty

    # relative to surface, surface given
    stats = GxgStats(ts, surface)
    res = stats.xg(reference='surface')
    assert isinstance(res, DataFrame)
    assert not res.empty

    # relative to surface, surface not given
    stats = GxgStats(ts)
    res = stats.xg(reference='surface')
    assert isinstance(res, DataFrame)
    assert not res.empty


def test_ghg(ts, surface):
  
    # with time series
    stats = GxgStats(ts)
    res = stats.ghg()
    assert isinstance(res, float)
    assert not np.isnan(res)

    stats = GxgStats(ts, surface=surface)
    res = stats.ghg(reference='surface')
    assert isinstance(res, float)
    assert not np.isnan(res)

    # without time series
    stats = GxgStats()
    res = stats.ghg()
    assert isinstance(res, float)
    assert np.isnan(res)


def test_glg(ts, surface):
  
    # with time series
    stats = GxgStats(ts)
    res = stats.glg()
    assert isinstance(res, float)
    assert not np.isnan(res)

    stats = GxgStats(ts, surface=surface)
    res = stats.glg(reference='surface')
    assert isinstance(res, float)
    assert not np.isnan(res)

    # without time series
    stats = GxgStats()
    res = stats.glg()
    assert isinstance(res, float)
    assert np.isnan(res)


def test_gt(ts, surface):

    # with series and surface
    stats = GxgStats(ts, surface)
    gt = stats.gt()
    isinstance(gt, str)

    # with series, without surface
    stats = GxgStats(ts)
    gt = stats.gt()
    assert np.isnan(gt)

    # without series, without surface
    stats = GxgStats()
    gt = stats.gt()
    assert np.isnan(gt)


def test_gxg(ts):

    # with time series
    stats = GxgStats(ts)
    res = stats.gxg(reference='datum', minimal=False)
    assert isinstance(res, Series)
    assert not res.empty

    stats = GxgStats(ts)
    res = stats.gxg(reference='surface', minimal=False)
    assert isinstance(res, Series)
    assert not res.empty

    stats = GxgStats(ts)
    res = stats.gxg(reference='datum', minimal=True)
    assert isinstance(res, Series)
    assert not res.empty

    stats = GxgStats(ts)
    res = stats.gxg(reference='surface', minimal=True)
    assert isinstance(res, Series)
    assert not res.empty

    # without time series
    stats = GxgStats()
    res = stats.gxg()
    assert isinstance(res, Series)
    assert res.empty


def test_gvg_approximations(ts, surface):
    
    stats = GxgStats(ts, surface)
    for validation in ['strict', 'moderate', 'generous', 'naive']:
        sr = stats.gvg_approximations(reference='surface', validation=validation)
        assert isinstance(sr, Series)
        assert not sr.empty

    # without surface level given
    stats = GxgStats(ts)
    sr = stats.gvg_approximations(reference='surface')
    assert isinstance(sr, Series)
    assert all(sr.isnull())
    
    # without surface level and without time series
    stats = GxgStats()
    sr = stats.gvg_approximations(reference='surface')
    assert isinstance(sr, Series)
    assert all(sr.isnull())


def test_confidence_mean():
    stats = GxgStats()
    sr = Series([1,2,3,4,5,6,7,8,9])
    assert np.round(stats._confidence_mean(sr, alfa=0.05), 2)==2.11
    
    