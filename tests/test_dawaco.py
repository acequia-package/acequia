
import pytest
##import collections
##import numpy as np
from pandas import DataFrame
import pandas as pd

from acequia import Dawaco, GwSeries
import acequia as aq

srcpath = r'.\data\dawaco\small_dataset.xlsx'

@pytest.fixture
def daw():
    # test_from_excel()
    daw = Dawaco.from_excel(srcpath)
    assert isinstance(daw, Dawaco)
    assert isinstance(daw.rawdata, DataFrame)
    return daw

def test_len(daw):
    assert len(daw)!=0

def test_repr(daw):
    assert isinstance(repr(daw),str)

def test_filters(daw):
    filters = daw.filters
    assert isinstance(filters, list)
    assert len(filters)!=0

def test_get_gwseries(daw):
    loc, fil = daw.filters[0]
    gw = daw.get_gwseries(loc,fil)
    assert isinstance(gw, GwSeries)
    assert len(gw)!=0

def test_iteritems(daw):
    for gw in daw.iteritems():
        assert isinstance(gw, GwSeries)
