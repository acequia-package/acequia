
import os
import pytest
from pandas import DataFrame, Series
from acequia import GwSeries
from acequia.io import DinoGwsCsv

fdir = r".\data\dinogws\\"

@pytest.fixture
def dn():
    filename = os.listdir(fdir)[0]
    fpath = os.path.join(fdir, filename)
    dn = DinoGwsCsv(fpath)
    assert isinstance(dn, DinoGwsCsv)
    return dn

def test_repr(dn):
    assert isinstance(str(dn), str)

def test_len(dn):
    assert len(dn)!=0

def test_nitgcode(dn):
    assert isinstance(dn.nitgcode(), str)

def test_data(dn):
    df = dn.data()
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_header(dn):
    df = dn.header()
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_gwseries(dn):
    gw = dn.gwseries()
    assert isinstance(gw, GwSeries)
    assert not gw.tubeprops().empty
    assert not gw.locprops().empty
    assert not gw.heads().empty
