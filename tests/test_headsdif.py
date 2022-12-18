
import pytest
import numpy as np
from pandas import DataFrame
import pandas as pd
import matplotlib as mpl
from acequia import GwSeries,HeadsDif
import acequia as aq

@pytest.fixture
def gw1():
    dnpath = r'.\data\dinogws\B29A0848001_1.csv'
    return GwSeries.from_dinogws(dnpath)


@pytest.fixture
def gw2():
    dnpath = r'.\data\dinogws\B29A0848002_1.csv'
    return GwSeries.from_dinogws(dnpath)

@pytest.fixture
def gw3():
    dnpath = r'.\data\dinogws\B29A0848003_1.csv'
    return GwSeries.from_dinogws(dnpath)

@pytest.fixture
def hdf(gw1,gw2):
    locname = gw1.locname()
    refcol = gw1.name()
    return HeadsDif.from_series(heads=[gw1,gw2],locname=locname,
        refcol=refcol)

   
def test_from_series(gw1,gw2):
    """Test classmethod from_series with different input."""

    # test with gwseries
    hdf = HeadsDif.from_series(heads=[gw1,gw2],locname=None,refcol=None)
    assert isinstance(hdf.heads,DataFrame)
    assert not hdf.heads.empty

    # test with pandas series
    sr1 = gw1.heads()
    sr2 = gw2.heads()
    hdf = HeadsDif.from_series(heads=[sr1,sr2],locname=None,refcol=None)
    assert isinstance(hdf.heads,DataFrame)
    assert not hdf.heads.empty
    
    # test UserWarning for invalid refcol
    with pytest.warns(UserWarning) as record:
        hdf = HeadsDif.from_series(heads=[gw1,gw2],locname=None,
            refcol='onzinkolom')
        assert len(record)==1


def test_repr(hdf):
    assert isinstance(hdf.__repr__(),str)


def test_get_difference(hdf):

    assert isinstance(hdf.get_difference(),DataFrame)
    assert not hdf.get_difference().empty
    
    # test UserWarning for invalid refcol
    with pytest.warns(UserWarning) as record:
         hdf.get_difference(refcol='onzinkolom')
         assert len(record)==1

def test_relative_heads(hdf):
    relheads = hdf.get_relative_heads()
    assert isinstance(relheads,DataFrame)
    assert not relheads.empty

def test_get_seasons(hdf):

    seasons = hdf.get_seasons()
    assert len(seasons)!=0
    
    seasons = hdf.get_seasons(period='seasons')
    assert len(seasons)!=0

    seasons = hdf.get_seasons(period='biannual')
    assert len(seasons)!=0

    seasons = hdf.get_seasons(dates=hdf.heads)
    assert len(seasons)!=0

    seasons = hdf.get_seasons(dates=hdf.heads.index)
    assert len(seasons)!=0

def test_get_difference_by_season(hdf):

    df = hdf.get_difference_by_season()
    assert isinstance(df,DataFrame)

    with pytest.warns(UserWarning) as record:
        df = hdf.get_difference_by_season(period='foute invoer')
        assert len(record)==1

    df = hdf.get_difference_by_season(period=hdf.PERIOD_DEFAULT)
    assert isinstance(df,DataFrame)

    for season in hdf.PERIOD_NAMES:
        df = hdf.get_difference_by_season(period=season)
        assert isinstance(df,DataFrame)
        assert not df.empty

def test_plot_time(gw1,gw2,gw3):

    hdf = HeadsDif.from_series(heads=[gw1,gw2,gw3])
    axlist = hdf.plot_time()
    assert isinstance(axlist,np.ndarray)
    for ax in axlist.flatten():
        assert isinstance(ax,mpl.axes._subplots.Axes)

def test_plot_head(gw1,gw2,gw3):

    hdf = HeadsDif.from_series(heads=[gw1,gw2,gw3])
    axlist = hdf.plot_head()
    assert isinstance(axlist,np.ndarray)
    for ax in axlist.flatten():
        assert isinstance(ax,mpl.axes._subplots.Axes)

def test_plot_freq(gw1,gw2,gw3):

    hdf = HeadsDif.from_series(heads=[gw1,gw2,gw3])
    axlist = hdf.plot_freq()
    assert isinstance(axlist,np.ndarray)
    for ax in axlist.flatten():
        assert isinstance(ax,mpl.axes._subplots.Axes)
