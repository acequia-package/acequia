import pytest
from datetime import datetime
from pandas import DataFrame, Series
from acequia import DinoGws
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

def test_parse_dino_date(dn):
    assert isinstance(dn.parse_dino_date('17-08-2009'),datetime)

def test__readheader(dn):
    assert isinstance(dn._readheader(),DataFrame)
    assert not dn._readheader().empty

def test__readgws(dn):
    assert isinstance(dn._readgws(),DataFrame)
    assert not dn._readgws().empty

def test_series(dn):
    assert isinstance(dn.series(),Series)
    assert not dn.series().empty
    assert isinstance(dn.series(units='cmmv'),Series)
    assert not dn.series(units='cmmv').empty
    assert isinstance(dn.series(units='cmmp'),Series)
    assert not dn.series(units='cmmp').empty
    assert isinstance(dn.series(units='cmnap'),Series)
    assert not dn.series(units='cmnap').empty
    
def test_headdata(dn):
    assert isinstance(dn.headdata(),DataFrame)
    assert not dn.headdata().empty

def test_header(dn):
    assert isinstance(dn.header(),DataFrame)
    assert not dn.header().empty

def test_data(dn):
    assert isinstance(dn.data(),DataFrame)
    assert not dn.data().empty

def test_locname(dn):
    assert isinstance(dn.locname(),str)
    assert len(dn.locname())!=0

def test_filname(dn):
    assert isinstance(dn.filname(),str)
    assert len(dn.filname())!=0

def test_srname(dn):
    assert isinstance(dn.srname(),str)
    assert len(dn.srname())!=0

def test_describe(dn):
    assert isinstance(dn.describe(),DataFrame)
    assert not dn.describe().empty

def test_locations(dn):
    assert dn.locations().empty

def test_merge(dn):
    assert isinstance(dn,DinoGws)

def test_filesfromdir(fdir=fdir):
    res = filesfromdir(r'.\data\dinogws\\')
    assert isinstance(res,tuple)
    assert len(res)==2


