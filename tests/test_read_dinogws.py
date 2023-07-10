import pytest
from datetime import datetime
from pandas import DataFrame, Series
from acequia import DinoGws, GwSeries
from acequia.read.dinogws import filesfromdir

fpath = r'.\data\dinogws\B28A0475002_1.csv'
fdir = r'.\data\dinogws\\'

@pytest.fixture
def dn():
    dn = DinoGws(filepath=fpath,readall=True)
    assert isinstance(dn,DinoGws)
    return dn

def test_repr(dn):
    assert isinstance(str(dn),str)

def test_parse_dino_date(dn):
    assert isinstance(dn.parse_dino_date('17-08-2009'),datetime)

def test_get_heads(dn):
    assert isinstance(dn.get_heads(),Series)
    assert not dn.get_heads().empty
    assert isinstance(dn.get_heads(units='cmmv'),Series)
    assert not dn.get_heads(units='cmmv').empty
    assert isinstance(dn.get_heads(units='cmmp'),Series)
    assert not dn.get_heads(units='cmmp').empty
    assert isinstance(dn.get_heads(units='cmnap'),Series)
    assert not dn.get_heads(units='cmnap').empty
    
def test_headdata(dn):
    assert isinstance(dn.headdata,DataFrame)
    assert not dn.headdata.empty

def test_header(dn):
    assert isinstance(dn.header,DataFrame)
    assert not dn.header.empty

def test_data(dn):
    assert isinstance(dn.data,DataFrame)
    assert not dn.data.empty

def test_gwseries(dn):
    gw = dn.gwseries
    assert isinstance(gw, GwSeries)
    assert not gw.heads().empty
    assert not gw.tubeprops().empty
    assert not gw.locprops().empty

def test_locname(dn):
    assert isinstance(dn.locname,str)
    assert len(dn.locname)!=0

def test_filname(dn):
    assert isinstance(dn.filname,str)
    assert len(dn.filname)!=0

def test_srname(dn):
    assert isinstance(dn.srname,str)
    assert len(dn.srname)!=0

def test_describe(dn):
    assert isinstance(dn.describe,DataFrame)
    assert not dn.describe.empty

def test_locations(dn):
    assert dn.get_locations().empty

def test_merge(dn):
    assert isinstance(dn,DinoGws)

def test_filesfromdir(fdir=fdir):
    res = filesfromdir(r'.\data\dinogws\\')
    assert isinstance(res,tuple)
    assert len(res)==2


# test private methods

def test__readfile(dn):
    res = dn._readfile(filepath=dn.filepath)
    assert isinstance(res,list)
    assert len(res)!=0

def test__readlines(dn):
    res = dn._readlines()
    assert isinstance(res,tuple)
    assert len(res)==2

def test__findlines(dn):
    res = dn._findlines()
    assert isinstance(res,tuple)
    assert len(res)==3

def test__readheader(dn):
    assert isinstance(dn._readheader(),DataFrame)
    assert not dn._readheader().empty

def test__readgws(dn):
    assert isinstance(dn._readgws(),DataFrame)
    assert not dn._readgws().empty

