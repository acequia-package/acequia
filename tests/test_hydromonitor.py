import pytest
from acequia import HydroMonitor, GwSeries
from pandas import Series, DataFrame

fpath = r'.\data\hymon\hydromonitor_testdata.csv'

@pytest.fixture
def hm():
    return HydroMonitor(fpath)

def test_repr(hm):
    assert isinstance(hm,HydroMonitor)
    assert isinstance(str(hm),str)


# test pulbic methods
# -------------------

def test_idkeys(hm):
    assert isinstance(hm.idkeys(),list)

def test_delete_duplicate_data(hm):
    res = hm.delete_duplicate_data()
    assert not res.empty

def test_get_series(hm):
    gws = hm.get_series(loc='B29A0072',fil='1')    
    assert isinstance(gws,GwSeries)

def test_to_list(hm):
    res = hm.to_list()
    assert isinstance(res,list)
    assert isinstance(res[0],GwSeries)

def test_to_json(hm):
    hm.to_json(r'.\output\json\\')

def test_iterdata(hm):
    rownr = 0
    for idx,row in hm.iterdata():
        assert len(idx)!=0
        assert len(row)!=0
        rownr+=1
    assert(rownr>0)

# test private methods
# --------------------

def test__readcsv(hm):
    header, line_numbers = hm._readcsv(fpath)
    assert not header.empty
    assert isinstance(line_numbers,tuple)

def test__read_header(hm):
    textfile = open(fpath)
    header, line_numbers = hm._read_header(textfile)
    assert not header.empty
    assert isinstance(line_numbers,tuple)
    assert len(line_numbers)==3

def test__read_metadata(hm):
    res = hm._read_metadata()
    assert not res.empty

def test__read_data(hm):
    res = hm._read_data()
    assert not res.empty





