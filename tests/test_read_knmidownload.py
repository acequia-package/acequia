

import pytest
from pandas import DataFrame
from acequia import KnmiDownload


def test__request_weather():
    """Request weather date from server""" 
    stn = KnmiDownload()
    res = stn._request_weather(par=None)
    assert res.status_code==200

def test__request_precipitation():
    """Request weather date from server""" 
    stn = KnmiDownload()
    res = stn._request_precipitation(par=None)
    assert res.status_code==200

def test_download_with_weather():
    stn = KnmiDownload()
    data = stn.download(kind='weather',result='data')
    assert isinstance(data,DataFrame)
    text = stn.download(kind='weather',result='text')
    assert isinstance(text,str)

def test_download_with_prc():
    stn = KnmiDownload()
    data = stn.download(kind='prc')
    assert isinstance(data,DataFrame)
    text = stn.download(kind='prc',result='text')
    assert isinstance(text,str)

def test_wtr_stns():
    stn = KnmiDownload()
    wtr = stn.wtr_stns
    assert isinstance(wtr,DataFrame)
    assert not wtr.empty

def test_prc_stns():
    stn = KnmiDownload()
    prc = stn.prc_stns
    assert isinstance(prc,DataFrame)
    assert not prc.empty
