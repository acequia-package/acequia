

import pytest
from pandas import Series, DataFrame
from geopandas import GeoDataFrame

from acequia.io import _brorest as brorest
from acequia.io import BroGwCollection
from acequia.tools import convert_RDtoWGS84
from acequia import GwSeries

@pytest.fixture
def gwc():
    gwc = BroGwCollection.from_rectangle(
        xmin = 259500,
        xmax = 259650,
        ymin = 489950,
        ymax = 490100,
        title = 'Agelerbroek',
        )
    return gwc

@pytest.fixture
def outfolder():
    return r".\output\json\\"

def test_len(gwc):
    assert len(gwc)!=0

def test_repr(gwc):
    assert isinstance(repr(gwc), str)

def test_tubes(gwc):
    assert isinstance(gwc.tubes(), list)
    assert len(gwc.tubes())!=0

def test_wells(gwc):
    assert isinstance(gwc.wells(), list)
    assert len(gwc.wells())!=0

def test_empty(gwc):
    assert not gwc.empty

def test_wellprops(gwc):
    df = gwc.wellprops(geo=False)
    assert isinstance(df, DataFrame)
    assert not df.empty

    gdf = gwc.wellprops(geo=True)
    assert isinstance(gdf, GeoDataFrame)
    assert not gdf.empty

def test_gwseries(gwc):
    gwname = gwc.tubes()[0]
    gw = gwc.gwseries(gwname)
    assert isinstance(gw, GwSeries)
    assert not gw.tubeprops().empty

def test_iteritems(gwc):
    for gw in gwc.iteritems():
        assert isinstance(gw, GwSeries)

def test_iter(gwc):
    for gw in gwc:
        assert isinstance(gw, GwSeries)

def test_tofolder(gwc, outfolder):
    gwc.to_folder(outfolder)
