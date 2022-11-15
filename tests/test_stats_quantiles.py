

import pytest
from pandas import DataFrame
import pandas as pd
import matplotlib
from acequia import Quantiles
from acequia import GwSeries

@pytest.fixture
def gw():
    fpath = r'.\data\dinogws\B21A0138001_1.csv'
    return GwSeries.from_dinogws(fpath)


def test_init(gw):

    # input gwseries object
    cum = Quantiles(gw)
    assert cum.__class__.__name__=='Quantiles'

    # input pandas Series object
    sr = gw.heads(ref='datum')
    cum = Quantiles(sr)
    assert cum.__class__.__name__=='Quantiles'

    # input pandas DataFrame object
    df = DataFrame(gw.heads(ref='datum'))
    cum = Quantiles(sr)
    assert cum.__class__.__name__=='Quantiles'

def test_quantiles(gw):

    cum = Quantiles(gw)

    # unit is days, step is valid
    quantiles = cum.quantiles(unit='days',step=30)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is days, step is invalid, default is used
    quantiles = cum.quantiles(unit='days',step=400)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty
    
    # unit is quantiles, step is valid
    quantiles = cum.quantiles(unit='quantiles',step=0.3)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is quantiles, step is invalid, default is used
    quantiles = cum.quantiles(unit='quantiles',step=3.0)
    assert isinstance(quantiles,DataFrame)
    assert not quantiles.empty

    # unit is invalid, exception is raised
    with pytest.raises(Exception):
        quantiles = cum.quantiles(unit='invalid_input')

def test_plot(gw):

    cum = Quantiles(gw)
    
    # plot with defaults
    myplot = cum.plot()
    assert isinstance(myplot,matplotlib.axes.Subplot)
    
    # test parameter coloryears
    myplot = cum.plot(coloryears=[2002,2007])
    assert isinstance(myplot,matplotlib.axes.Subplot)

    # test boundyears
    myplot = cum.plot(boundyears=[2004,2005])
    assert isinstance(myplot,matplotlib.axes.Subplot)
    
    # test figpath
    myplot = cum.plot(figpath=r'.\output\fig\duurlijnen.jpg')
    assert isinstance(myplot,matplotlib.axes.Subplot)
