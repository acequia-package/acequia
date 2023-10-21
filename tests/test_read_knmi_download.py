

import pytest
from pandas import Series, DataFrame
from geopandas import GeoDataFrame
from acequia import KnmiDownload
from acequia import get_knmi_evaporation, get_knmi_precipitation
from acequia import get_knmi_weatherstations, get_knmi_precstations


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
    data = stn.get_rawdata(kind='precipitation')
    assert isinstance(data,DataFrame)
    text = stn.get_rawdata(kind='precipitation', result='text')
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
    data = knmi.get_precipitation(station='327', name=None, start=None, end=None)
    assert isinstance(data,Series)
    assert not data.empty

    data = knmi.get_precipitation(name='Finsterwolde', start=None, end=None)
    assert isinstance(data,Series)
    assert not data.empty

    sr = knmi.get_precipitation(name='Nieuw Beerta', kind='weather')
    assert isinstance(sr, Series)
    assert not sr.empty

    with pytest.raises(ValueError):
        knmi.get_precipitation(name='Nieuw Beerta', kind='wrong type')

    with pytest.raises(ValueError):
        knmi.get_precipitation(name='Nieuw Beerta', kind='precipitation')

    with pytest.raises(ValueError):
        knmi.get_precipitation(station=None, name=None, kind='weather')

def test_get_evaporation():
    knmi = KnmiDownload()

    sr = knmi.get_evaporation(name='Nieuw Beerta')
    assert isinstance(sr, Series)
    assert not sr.empty

    sr = knmi.get_evaporation(station='286')   
    assert isinstance(sr, Series)
    assert not sr.empty

    with pytest.raises(ValueError):
        knmi.get_evaporation(station=None, name=None)    
    
    with pytest.raises(ValueError):
        knmi.get_evaporation(name='Nergenshuizen')

def test_get_weather():
    knmi = KnmiDownload()
    data = knmi.get_weather(station='260', name=None, start=None, end=None)
    assert isinstance(data,DataFrame)
    assert not data.empty

    data = knmi.get_weather(name='De Bilt', start=None, end=None)
    assert isinstance(data,DataFrame)
    assert not data.empty

def test_get_station_metadata():

    knmi = KnmiDownload()
    
    sr = knmi.get_station_metadata('745')
    assert isinstance(sr, Series)
    assert not sr.empty

    sr = knmi.get_station_metadata('999')
    assert isinstance(sr, Series)
    assert sr.empty

    sr = knmi.get_station_metadata('260', kind='weather')
    assert isinstance(sr, Series)
    assert not sr.empty

    sr = knmi.get_station_metadata('999', kind='weather')
    assert isinstance(sr, Series)
    assert sr.empty

def test_get_station_code():

    knmi = KnmiDownload()

    code = knmi.get_station_code('Zwolle')
    assert isinstance(code, str)

    code = knmi.get_station_code('Nergenshuizen')
    assert code is None

    code = knmi.get_station_code('Nieuw Beerta', kind='weather')
    assert isinstance(code, str)

    code = knmi.get_station_code('Nergenshuizen', kind='weather')
    assert code is None

def test_get_distance():

    PREC_STN_COUNTS = 329
    WTR_STN_COUNTS = 36
    LATLON = (52.51221297354996, 6.089788276983239)
    XY = (202694.86683117278, 502957.1681540037)

    knmi = KnmiDownload()

    # input: weather station code
    ds = knmi.get_distance(kind='weather', stn=knmi.DEFAULT_WTR)
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS # test breaks if knmi changes number of stations

    # input: precipitation station code
    ds = knmi.get_distance(kind='precipitation', stn=knmi.DEFAULT_PREC)
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS # test breaks if knmi changes number of stations

    # inut: station name
    ds = knmi.get_distance(kind='weather', name='Heino')
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='precipitation', name='Zwolle')
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

    # input: xy
    ds = knmi.get_distance(kind='weather', xy=(XY[0], XY[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='precipitation', xy=(XY[0], XY[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

    # input: latlon
    ds = knmi.get_distance(kind='weather', latlon=(LATLON[0], LATLON[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==WTR_STN_COUNTS

    ds = knmi.get_distance(kind='precipitation', latlon=(LATLON[0], LATLON[1]))
    assert isinstance(ds, DataFrame)
    assert not ds.empty
    assert len(ds)==PREC_STN_COUNTS

def test_nan_replacements():

    knmi = KnmiDownload()
    startdate = '19720115'
    enddate = '19720215'
    prec = knmi.get_precipitation(name='Finsterwolde', start=startdate, end=enddate, fillnans=False)
    sr, repldata = knmi.replace_missing_values(kind='precipitation', meteo=prec)
    assert isinstance(sr, Series)
    assert sr[sr.isnull()].empty
    assert isinstance(repldata, DataFrame)
    assert not repldata.empty

    knmi = KnmiDownload()
    startdate = '19900101'
    enddate = '19900301'
    df = knmi.get_weather(name='Nieuw Beerta', start=startdate, end=enddate, fillnans=False)
    sr = df['evap'].squeeze()
    sr.name = '286'
    sr, repldata = knmi.replace_missing_values(kind='weather', meteo=sr)
    assert isinstance(sr, Series)
    assert sr[sr.isnull()].empty
    assert isinstance(repldata, DataFrame)
    assert not repldata.empty


def test_functions():

    sr = get_knmi_precipitation(station='327')
    assert isinstance(sr, Series)
    assert not sr.empty

    sr = get_knmi_evaporation(station='286')
    assert isinstance(sr, Series)
    assert not sr.empty

    data = get_knmi_precstations(geo=True)
    assert isinstance(data, GeoDataFrame)
    assert not data.empty

    data = get_knmi_precstations(geo=False)
    assert isinstance(data, DataFrame)
    assert not data.empty

    data = get_knmi_weatherstations(geo=True)
    assert isinstance(data, GeoDataFrame)
    assert not data.empty

    data = get_knmi_weatherstations(geo=False)
    assert isinstance(data, DataFrame)
    assert not data.empty

def test_duplicates():

    knmi = KnmiDownload()
    df = knmi.duplicate_station_names
    assert isinstance(df, DataFrame)
    assert not df.empty
    assert len(df)==23 # breaks if knmi changes number of stations

    knmi = KnmiDownload()
    df = knmi.duplicate_station_codes
    assert isinstance(df, DataFrame)
    assert not df.empty
    assert len(df)==13 # breaks if knmi changes number of stations

