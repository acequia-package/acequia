

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
    data = knmi.get_weather_stations()
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_prc_stns():
    knmi = KnmiDownload()
    data = knmi.get_precipitation_stations()
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_get_precipitation():
    knmi = KnmiDownload()
    data = knmi.get_precipitation(station='327', location=None, start=None, end=None)
    assert isinstance(data,Series)
    assert not data.empty

    data = knmi.get_precipitation(location='Finsterwolde', start=None, end=None)
    assert isinstance(data,Series)
    assert not data.empty


def test_get_weather():
    knmi = KnmiDownload()
    data = knmi.get_weather(station='260', location=None, start=None, end=None)
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = knmi.get_weather(location='De Bilt', start=None, end=None)
    assert isinstance(data,DataFrame)
    assert not data.empty


def test_get_distance():

    PREC_STN_COUNTS = 329
    WTR_STN_COUNTS = 36
    LATLON = (52.51221297354996, 6.089788276983239)
    XY = (202694.86683117278, 502957.1681540037)

    knmi = KnmiDownload()

    # input: weather station code
    ds = knmi.get_distance(kind='wtr', stn=knmi.DEFAULT_WTR)
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS # test breaks if knmi changes number of stations

    # input: precipitation station code
    ds = knmi.get_distance(kind='prec', stn=knmi.DEFAULT_PREC)
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS # test breaks if knmi changes number of stations

    # inut: station name
    ds = knmi.get_distance(kind='wtr', location='Heino')
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='prec', location='Zwolle')
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

    # input: xy
    ds = knmi.get_distance(kind='wtr', xy=(XY[0], XY[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='prec', xy=(XY[0], XY[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

    # input: latlon
    ds = knmi.get_distance(kind='wtr', latlon=(LATLON[0], LATLON[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='prec', latlon=(LATLON[0], LATLON[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

def test_nan_replacements():

    knmi = KnmiDownload()
    startdate = '19720601'
    enddate = '19720801'
    prec = knmi.get_precipitation(location='Finsterwolde', start=startdate, end=enddate)
    sr = knmi.replace_missing_values(kind='prec', meteo=prec)
    assert isinstance(sr, Series)
    assert sr[sr.isnull()].empty
    assert isinstance(knmi._nan_replacements, DataFrame)
    assert not knmi._nan_replacements.empty

    knmi = KnmiDownload()
    startdate = '19900101'
    enddate = '19900301'
    df = knmi.get_weather(location='Nieuw Beerta', start=startdate, end=enddate)
    sr = df['evap'].squeeze()
    sr.name = '286'
    sr = knmi.replace_missing_values(kind='wtr', meteo=sr)
    assert isinstance(sr, Series)
    assert sr[sr.isnull()].empty
    assert isinstance(knmi._nan_replacements, DataFrame)
    assert not knmi._nan_replacements.empty


def test_functions():

    data = get_knmiprc()
    assert isinstance(data,Series)
    assert not data.empty

    data = get_knmiwtr()
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = get_knmiprc_stn(geo=True)
    assert isinstance(data,GeoDataFrame)
    assert not data.empty

    data = get_knmiwtr_stn()
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = get_knmiprc_stn(geo=True)
    assert isinstance(data,GeoDataFrame)
    assert not data.empty

    data = get_knmiwtr_stn()
    assert isinstance(data,DataFrame)
    assert not data.empty

