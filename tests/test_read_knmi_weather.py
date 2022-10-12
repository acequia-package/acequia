
import pytest
#import numpy as np
from pandas import DataFrame, Series
#import pandas as pd
#import acequia as aq
from acequia import KnmiWeather

fpath = r'.\data\knmi_weather\etmgeg_251.txt' 

@pytest.fixture
def wtr():
    return KnmiWeather.from_file(fpath)

def test_repr(wtr):
    print(wtr)

def test_rawdata(wtr):
    assert isinstance(wtr.rawdata,DataFrame)
    assert not wtr.rawdata.empty

def test_data(wtr):
    assert isinstance(wtr.data,DataFrame)
    assert not wtr.data.empty

def test_desc(wtr):
    assert isinstance(wtr.desc,DataFrame)
    assert not wtr.desc.empty

def test_stn(wtr):
    assert isinstance(wtr.stn,int)

def test_units(wtr):
    assert isinstance(wtr.units,DataFrame)
    assert not wtr.units.empty

def test_timeseries(wtr):
    assert isinstance(wtr.timeseries(),Series)
    assert not wtr.timeseries().empty
    assert isinstance(wtr.timeseries(var='prc'),Series)
    assert not wtr.timeseries(var='prc').empty
    assert isinstance(wtr.timeseries(var='evp'),Series)
    assert not wtr.timeseries(var='evp').empty
    assert isinstance(wtr.timeseries(var='rch'),Series)
    assert not wtr.timeseries(var='rch').empty

def test_prc(wtr):
    assert isinstance(wtr.prc,Series)
    assert not wtr.prc.empty

def test_evp(wtr):
    assert isinstance(wtr.evp,Series)
    assert not wtr.evp.empty

def test_recharge(wtr):
    assert isinstance(wtr.recharge,Series)
    assert not wtr.recharge.empty
