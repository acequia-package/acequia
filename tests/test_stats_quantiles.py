

import pytest
from pandas import Series, DataFrame
import pandas as pd
import matplotlib
from acequia import Quantiles
from acequia import GwSeries

fpath = r'.\data\dinogws\B21A0138001_1.csv'

@pytest.fixture
def gw():
    return GwSeries.from_dinogws(fpath)


def test_init(gw):

    # input gwseries object
    qt = Quantiles(gw)
    assert qt.__class__.__name__=='Quantiles'

    # input pandas Series object
    sr = gw.heads(ref='datum')
    qt = Quantiles(sr)
    assert qt.__class__.__name__=='Quantiles'

    # input pandas DataFrame object
    df = DataFrame(gw.heads(ref='datum'))
    qt = Quantiles(sr)
    assert qt.__class__.__name__=='Quantiles'
    

@pytest.fixture
def qt():
    gw = GwSeries.from_dinogws(fpath)
    return Quantiles(gw)

@pytest.fixture
def qt2():
    gw = GwSeries.from_dinogws(fpath)
    return Quantiles(gw)


def test_quantiles(qt):

    # unit is days, step is valid
    quantiles = qt.get_quantiles(unit='days',step=30)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is days, step is invalid, default is used
    quantiles = qt.get_quantiles(unit='days',step=400)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty
    
    # unit is quantiles, step is valid
    quantiles = qt.get_quantiles(unit='quantiles',step=0.3)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is quantiles, step is invalid, default is used
    quantiles = qt.get_quantiles(unit='quantiles',step=3.0)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is invalid, exception is raised
    with pytest.raises(Exception):
        quantiles = qt.get_quantiles(unit='invalid_input')

def test_headsref(qt):
    assert isinstance(qt.headsref,str)

def test_summary(qt):

    summary = qt.get_summary()
    assert isinstance(summary,DataFrame)
    assert not summary.empty

def test_get_inundation(qt2):

    sr = qt2.get_inundation()
    assert isinstance(sr,Series)
    assert not sr.empty

def test_get_lowest(qt2):

    sr = qt2.get_lowest()
    assert isinstance(sr,Series)
    assert not sr.empty

def test_repr(qt):
    assert isinstance(str(qt),str)

def test_plot(qt):

    # plot with defaults
    myplot = qt.plot()
    assert isinstance(myplot,matplotlib.axes.Subplot)
    
    # test parameter coloryears
    myplot = qt.plot(coloryears=[2002,2007])
    assert isinstance(myplot,matplotlib.axes.Subplot)

    # test boundyears
    myplot = qt.plot(boundyears=[2004,2005])
    assert isinstance(myplot,matplotlib.axes.Subplot)
    
    # test figpath
    myplot = qt.plot(figpath=r'.\output\fig\duurlijnen.jpg')
    assert isinstance(myplot,matplotlib.axes.Subplot)

