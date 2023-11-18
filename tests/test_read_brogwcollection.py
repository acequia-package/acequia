

import pytest
from pandas import Series, DataFrame

from acequia import _brorest as brorest
from acequia import BroGwCollection
from acequia import geo_convert_RDtoWGS84
from acequia import GwSeries

@pytest.fixture
def gwc():

    lowerleft = geo_convert_RDtoWGS84(258880,489330)
    upperright = geo_convert_RDtoWGS84(259375,489750)

    gwc = BroGwCollection.from_rectangle(
        xmin = lowerleft[0], 
        xmax = upperright[0],
        ymin = lowerleft[1],
        ymax = upperright[1],
        name = 'Agelerbroek',
        )

    return gwc

def test_wells(gwc):
    df = gwc.wells
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_tubes(gwc):
    df = gwc.tubes
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_get_gwseries(gwc):

    # test with gmwid
    gmwid = gwc._tubes.at[0,'gmwid']
    tube = gwc._tubes.at[0,'tubenr']

    gw = gwc.get_gwseries(gmwid=gmwid, wellcode=None, tube=tube)
    assert isinstance(gw, GwSeries)
    assert not gw.tubeprops().empty

    # test with wellcode
    wellcode = gwc._wells.loc[0,'wellcode']
    idx = gwc._wells[gwc._wells['wellcode']==wellcode].index[0]
    gmwid = gwc._wells.loc[idx,'gmwid']
    idx = gwc._tubes[gwc._tubes['gmwid']==gmwid].index[0]
    tube = gwc._tubes.loc[idx,'tubenr']

    gw = gwc.get_gwseries(gmwid=None, wellcode=wellcode, tube=tube)
    assert isinstance(gw, GwSeries)
    assert not gw.tubeprops().empty

def test_iteritems(gwc):
    for gw in gwc.iteritems():
        assert isinstance(gw.name(), str)
