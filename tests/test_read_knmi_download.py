

import pytest
from pandas import Series, DataFrame
from geopandas import GeoDataFrame
from acequia import KnmiDownload
from acequia import get_knmiwtr, get_knmiprc
from acequia import get_knmiwtr_stn, get_knmiprc_stn

def test_bad_request_weather():
    """Request weather date from server""" 
    stn = KnmiDownload()
    res = stn._request_weather(par=None)
    assert res.status_code==200

def test_bad_request_precipitation():
    """Request weather date from server""" 
    stn = KnmiDownload()
    res = stn._request_precipitation(par=None)
    assert res.status_code==200

def test_download_with_weather():
    stn = KnmiDownload()
    data = stn.get_rawdata(kind='weather',result='data')
    assert isinstance(data,DataFrame)
    text = stn.get_rawdata(kind='weather',result='text')
    assert isinstance(text,str)

def test_download_with_prc():
    stn = KnmiDownload()
    data = stn.get_rawdata(kind='prec')
    assert isinstance(data,DataFrame)
    text = stn.get_rawdata(kind='prec',result='text')
    assert isinstance(text,str)

def test_wtr_stns():
    knmi = KnmiDownload()
    data = knmi.weather_stations
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_prc_stns():
    knmi = KnmiDownload()
    data = knmi.precipitation_stations
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_get_precipitation():
    knmi = KnmiDownload()
    data = knmi.get_precipitation(station='327', location=None, start=None, end=None)
    assert isinstance(data,Series)
    assert not data.empty

def test_get_weather():
    knmi = KnmiDownload()
    data = knmi.get_weather(station='260', location=None, start=None, end=None)
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_functions():

    data = get_knmiprc()
    assert isinstance(data,Series)
    assert not data.empty

    data = get_knmiwtr()
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = get_knmiprc_stn(geodataframe=True)
    assert isinstance(data,GeoDataFrame)
    assert not data.empty

    data = get_knmiwtr_stn(geodataframe=False)
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = get_knmiprc_stn(geodataframe=True)
    assert isinstance(data,GeoDataFrame)
    assert not data.empty

    data = get_knmiwtr_stn(geodataframe=False)
    assert isinstance(data,DataFrame)
    assert not data.empty

