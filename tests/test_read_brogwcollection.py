

import pytest
from pandas import Series, DataFrame

from acequia import _brorest as brorest
from acequia import BroGwCollection
from acequia import geo_convert_RDtoWGS84
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


# test magic mathods

def test_len(gwc):
    assert len(gwc)!=0

def test_repr(gwc):
    assert isinstance(repr(gwc), str)

# test properties

def test_names(gwc):
    assert isinstance(gwc.names, list)
    assert len(gwc.names)!=0

def test_loclist(gwc):
    assert isinstance(gwc.loclist, list)
    assert len(gwc.loclist)!=0

def test_empty(gwc):
    assert not gwc.empty

def test_wells(gwc):
    df = gwc.wells
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_tubes(gwc):
    df = gwc.tubes
    assert isinstance(df, DataFrame)
    assert not df.empty

# test methods

def test_get_gwseries(gwc):
    gwname = gwc.names[0]
    gw = gwc.get_gwseries(gwname)
    assert isinstance(gw, GwSeries)
    assert not gw.tubeprops().empty

def test_iteritems(gwc):
    for gw in gwc.iteritems():
        assert isinstance(gw.name(), str)
