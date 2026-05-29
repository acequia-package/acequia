
import pytest
import os
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
from acequia import GwSeries
import acequia as aq

dinodir = '.\\data\\dinogws\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'
figdir = '.\\output\\fig\\'
dnpath = f'{dinodir}B29A0850002_1.csv'


@pytest.fixture
def gw():
    ##return GwSeries.from_dinogws(dnpath)
    filename = os.listdir(jsondir)[0]
    fpath = os.path.join(jsondir, filename)
    return GwSeries.from_json(fpath)

@pytest.fixture
def name(gw):
    return gw.name()

def test_GwSeries_init():
    gwseries = GwSeries()
    assert isinstance(gwseries, GwSeries)

def test_len(gw):
    assert len(gw)!=0

def test_repr(gw):
    assert isinstance(repr(gw),str)

def test_empty():
    gw = GwSeries()
    assert gw.empty

"""
def test_GwSeries_from_dinogws(name):
    gwd = aq.GwSeries.from_dinogws(dnpath)
    assert gwd.name()==name
"""

def test_GwSeries_to_json(gw):
    gw.to_json(f'{jsondir}{gw.name()}.json')
    gw.to_json(jsondir)

def test_GwSeries_from_json(gw,name):
    gwj = aq.GwSeries.from_json(f'{jsondir}{gw.name()}.json')
    assert gwj.name()==name

def test_GwSeries_to_csv(gw):
    gw.to_csv(f'{csvdir}{gw.name()}.csv')

def test_GwSeries_name(gw,name):
    assert gw.name()==name

def test_GwSeries_locname(gw):
    assert isinstance(gw.locname(),str)

def test_GwSeries_locprops(gw):
    assert gw.locprops().index[0]==gw.locname()
    assert isinstance(gw.locprops(), GwSeries)
    assert isinstance(gw.locprops(as_dataframe=False), Series)

def test_GwSeries_tubeprops(gw,name):
    assert gw.tubeprops().iloc[0,0]==name
    assert len(gw.tubeprops(last=True))==1

def test_GwSeries_tubeprops_changes(gw):
    assert isinstance(gw.tubeprops_changes(),pd.Series)
    assert not gw.tubeprops_changes().empty

def test_GwSeries_surface(gw):
    assert isinstance(gw.surface(), float)

def test_GwSeries_heads(gw):
    assert isinstance(gw.heads(),pd.Series)
    assert not gw.heads().empty

def test_GwSeries_timestats(gw):
    assert isinstance(gw.timestats(),pd.Series)
    assert not gw.timestats().empty

def test_GwSeries_descibe(gw):
    assert isinstance(gw.describe(),pd.Series)
    assert not gw.describe().empty

def test_GwSeries_plotheads(gw):
    figpath = f'{figdir}plotheads.jpg'
    gw.plotheads(proptype='mplevel',filename=figpath)

def test_GwSeries_gxg(gw):
    gxgs = gw.gxg(ref='surface')
    gxgd = gw.gxg(ref='datum')
    assert isinstance(gxgs, pd.Series)
    assert isinstance(gxgd, pd.Series)
    assert not gxgs.empty
    assert not gxgd.empty
    assert gxgs['gxgref']=='surface'
    assert gxgd['gxgref']=='datum'
    assert gxgs['gt']==gxgd['gt']

def test_GwSeries_xg(gw):
    assert not gw.xg().empty

