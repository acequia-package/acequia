
import pytest
from pandas import DataFrame, Series
from acequia import KnmiRain

fpath = r'.\data\knmi_prc\550_debilt.txt'

@pytest.fixture
def prec():
    return KnmiRain(filepath=fpath)

def test_repr(prec):
    assert isinstance(repr(prec),str)

def test_rawdata(prec):
    assert isinstance(prec.rawdata,DataFrame)
    assert not prec.rawdata.empty

def test_data(prec):
    assert isinstance(prec.data,DataFrame)
    assert not prec.data.empty

def test_units(prec):
    assert isinstance(prec.units,DataFrame)
    assert not prec.units.empty

def test_get_timeseries(prec):
    assert isinstance(prec.get_timeseries(),Series)
    assert not prec.get_timeseries().empty
    assert isinstance(prec.get_timeseries(var='prec'),Series)
    assert not prec.get_timeseries(var='prec').empty
    assert isinstance(prec.get_timeseries(var='snow'),Series)
    assert not prec.get_timeseries(var='snow').empty

def test_header(prec):
    assert len(prec.header)!=0

def test_prc(prec):
    assert isinstance(prec.prec,Series)
    assert not prec.prec.empty

def test_snow(prec):
    assert isinstance(prec.snow,Series)
    assert not prec.snow.empty

def test_station(prec):
    assert isinstance(prec.station,str)

def test_location(prec):
    assert isinstance(prec.location,str)

def test_filepath(prec):
    assert isinstance(prec.filepath, str)

def test_period(prec):
    assert isinstance(prec.period, str)

