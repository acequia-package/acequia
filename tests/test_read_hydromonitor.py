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
    assert isinstance(hm.idkeys,list)

def test_delete_duplicate_data(hm):
    res = hm._delete_duplicate_data()
    assert not res.empty

def test_get_series(hm):
    gws = hm.get_series(loc='B29A0072',fil='1')    
    assert isinstance(gws,GwSeries)

def test_series(hm):
    assert isinstance(hm.series,list)
    assert len(hm.series)!=0

def test_locations(hm):
    assert isinstance(hm.locations,list)
    assert len(hm.locations)!=0

def test_to_list(hm):
    gwlist = hm.to_list()
    assert isinstance(gwlist,list)
    for i,gw in enumerate(gwlist):
        assert isinstance(gw,GwSeries)

def test_to_json(hm):
    hm.to_json(r'.\output\json\\')

"""
def test_iterdata(hm):
    rownr = 0
    for idx,row in hm.iterdata():
        assert len(idx)!=0
        assert len(row)!=0
        rownr+=1
    assert(rownr>0)
"""

def test_iteritems(hm):
    for gw in hm.iteritems():
        assert isinstance(gw, GwSeries)


# test private methods
# --------------------

def test__readcsv(hm):
    header, line_numbers, meta_colnames, data_colnames = hm._readcsv()
    assert not header.empty
    assert isinstance(line_numbers,Series)
    assert isinstance(meta_colnames,list)
    assert len(meta_colnames)!=0
    assert isinstance(data_colnames,list)
    assert len(data_colnames)!=0

def test__extract_contents(hm):
    metadata, data = hm._extract_contents()
    assert not metadata.empty
    assert not data.empty






