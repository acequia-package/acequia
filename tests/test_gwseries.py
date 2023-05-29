
import pytest
import numpy as np
import pandas as pd
import acequia as aq

dinodir = '.\\data\\dinogws\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'
figdir = '.\\output\\fig\\'
dnpath = f'{dinodir}B29A0850002_1.csv'


@pytest.fixture
def gws():
    return aq.GwSeries.from_dinogws(dnpath)


@pytest.fixture
def name(gws):
    return gws.name()


def test_GwSeries_init():
    gw = aq.GwSeries()
    assert isinstance(gw,aq.gwseries.GwSeries)


def test_GwSeries_from_dinogws(name):
    gwd = aq.GwSeries.from_dinogws(dnpath)
    assert gwd.name()==name


def test_GwSeries_to_json(gws):
    gws.to_json(f'{jsondir}{gws.name()}.json')
    gws.to_json(jsondir)

def test_GwSeries_from_json(gws,name):
    gwj = aq.GwSeries.from_json(f'{jsondir}{gws.name()}.json')
    assert gwj.name()==name


def test_GwSeries_to_csv(gws):
    gws.to_csv(f'{csvdir}{gws.name()}.csv')


def test_GwSeries_name(gws,name):
    assert gws.name()==name


def test_GwSeries_locname(gws):
    assert isinstance(gws.locname(),str)


def test_GwSeries_locprops(gws,name):
    assert gws.locprops().index[0]==name


def test_GwSeries_tubeprops(gws,name):
    assert gws.tubeprops().iloc[0,0]==name
    assert len(gws.tubeprops(last=True))==1


def test_GwSeries_tubeprops_changes(gws):
    assert isinstance(gws.tubeprops_changes(),pd.Series)
    assert not gws.tubeprops_changes().empty


def test_GwSeries_surface(gws):
    assert isinstance(gws.surface(),np.float64)


def test_GwSeries_heads(gws):
    assert isinstance(gws.heads(),pd.Series)
    assert not gws.heads().empty


def test_GwSeries_timestats(gws):
    assert isinstance(gws.timestats(),pd.Series)
    assert not gws.timestats().empty


def test_GwSeries_descibe(gws):
    assert isinstance(gws.describe(),pd.Series)
    assert not gws.describe().empty


def test_GwSeries_plotheads(gws):
    figpath = f'{figdir}plotheads.jpg'
    gws.plotheads(proptype='mplevel',filename=figpath)


def test_GwSeries_gxg(gws):
    gxgs = gws.gxg(ref='surface')
    gxgd = gws.gxg(ref='datum')
    assert isinstance(gxgs,pd.Series)
    assert isinstance(gxgd,pd.Series)
    assert not gxgs.empty
    assert not gxgd.empty
    assert gxgs['gxgref']=='surface'
    assert gxgd['gxgref']=='datum'
    assert gxgs['gt']==gxgd['gt']


def test_GwSeries_xg(gws):
    assert not gws.xg().empty

