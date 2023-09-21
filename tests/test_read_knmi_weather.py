
import pytest
from pandas import DataFrame, Series
from acequia import KnmiWeather

##fpath = r'.\data\knmi_weather\etmgeg_251.txt' 
fpath = r'.\data\knmi_weather\260_debilt.txt'

@pytest.fixture
def wtr():
    return KnmiWeather(filepath=fpath)

def test_repr(wtr):
    assert isinstance(repr(wtr),str)

def test_rawdata(wtr):
    assert isinstance(wtr.rawdata,DataFrame)
    assert not wtr.rawdata.empty

def test_data(wtr):
    assert isinstance(wtr.data,DataFrame)
    assert not wtr.data.empty

def test_variables(wtr):
    assert isinstance(wtr.variables,DataFrame)
    assert not wtr.variables.empty

def test_units(wtr):
    assert isinstance(wtr.units,DataFrame)
    assert not wtr.units.empty

def test_get_timeseries(wtr):
    assert isinstance(wtr.get_timeseries(),Series)
    assert not wtr.get_timeseries().empty
    assert isinstance(wtr.get_timeseries(var='prec'),Series)
    assert not wtr.get_timeseries(var='prec').empty
    assert isinstance(wtr.get_timeseries(var='evap'),Series)
    assert not wtr.get_timeseries(var='evap').empty
    assert isinstance(wtr.get_timeseries(var='rch'),Series)
    assert not wtr.get_timeseries(var='rch').empty

def test_prec(wtr):
    assert isinstance(wtr.prec,Series)
    assert not wtr.prec.empty

def test_evap(wtr):
    assert isinstance(wtr.evap,Series)
    assert not wtr.evap.empty

def test_recharge(wtr):
    assert isinstance(wtr.recharge,Series)
    assert not wtr.recharge.empty

def test_station(wtr):
    assert isinstance(wtr.station,str)

def test_location(wtr):
    assert isinstance(wtr.location,str)

def test_lon(wtr):
    assert isinstance(wtr.lon,str)

def test_lat(wtr):
    assert isinstance(wtr.lat,str)

def test_altitude(wtr):
    assert isinstance(wtr.altitude,str)


