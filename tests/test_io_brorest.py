

import pytest
from pandas import Series, DataFrame
from xml.etree.ElementTree import ElementTree

from acequia.io._brorest import BroREST
from acequia.io import _brorest
from acequia.io import BroGmwXml, BroGldXml


@pytest.fixture
def gmwid():
    return 'GMW000000041145'

@pytest.fixture
def gldid():
    return 'GLD000000010138'
    
@pytest.fixture
def bronhouderid():
    return '51048329'

@pytest.fixture
def center():
    return (269228.35,485925.98)

@pytest.fixture
def rect():
    rect = {}
    rect['xmin']=268550
    rect['xmax']=270000
    rect['ymin']=485000
    rect['ymax']=486700
    return rect

# Test module functions
# ---------------------

def test_get_bro_gmwcodes_from_area(center, rect):

    circle = _brorest.get_bro_gmwcodes_from_area(
        center=center,
        radius=0.5,
        )
    assert isinstance(circle,DataFrame)
    assert not circle.empty

    rectangle = _brorest.get_bro_gmwcodes_from_area(
        xmin=rect['xmin'],
        xmax=rect['xmax'],
        ymin=rect['ymin'],
        ymax=rect['ymax'],
        )
    assert isinstance(rectangle, DataFrame)
    assert not rectangle.empty

def get_bro_gmwprops(gmwid=None, description=None):
    tubes = _brorest.get_get_bro_gmwprops(gmwid)
    assert isinstance(tubes, DataFrame)
    assert not tubes.empty

def test_getgldfromgmw(gmwid):
    gldlist = _brorest.get_bro_gld_from_gmw(gmwid)
    assert isinstance(gldlist, DataFrame)
    assert len(gldlist)!=0

def test_getwellusername(gmwid):
    wellcode = _brorest.get_bro_gmw_username(gmwid)
    assert isinstance(wellcode, str)
    assert len(wellcode)!=0

def test_getgmwcodes(bronhouderid):
    gmwlist = _brorest.get_bro_gmwcodes_from_bronhouder(bronhouderid)
    assert isinstance(gmwlist,list)
    assert gmwlist


# Test object methods and properties
# ----------------------------------

def test_status_code(gmwid):

    brest = BroREST()   
    assert brest.status_code is None
   
    brest.get_gmw_username(gmwid=gmwid)
    assert isinstance(brest.status_code, int)

def test_status_reason(gmwid):

    brest = BroREST()   
    assert brest.status_reason is None
   
    brest.get_gmw_username(gmwid=gmwid)
    assert isinstance(brest.status_reason, str)

def test_get_gmwprops(gmwid):
    brest = BroREST()
    res = brest.get_gmwprops(gmwid=gmwid)
    assert isinstance(res, ElementTree)

def test_get_gld_from_gmw(gmwid):
    brest = BroREST()
    res = brest.get_gld_from_gmw(gmwid=gmwid)
    assert isinstance(res, DataFrame)
    assert not res.empty

def test_get_gmw_username(gmwid):
    brest = BroREST()
    res = brest.get_gmw_username(gmwid=gmwid)
    assert isinstance(res, str)


def test_get_gldxml(gldid):
    brest = BroREST()
    res = brest.get_gldxml(gldid=gldid)
    assert isinstance(res, ElementTree)


def test_get_gldcodes_from_bronhouder(bronhouderid):

    brest = BroREST()
    res = brest.get_gldcodes_from_bronhouder(bronhouderid)
    assert isinstance(res, list)
    assert res


def test_get_gmwcodes_from_bronhouder(bronhouderid):

    brest = BroREST()
    res = brest.get_gmwcodes_from_bronhouder(bronhouderid)
    assert isinstance(res, list)
    assert res


def test_gmwcodes_from_circle(center):

    brest = BroREST()
    circle = brest.get_gmwcodes_from_area(
        center=center,
        radius=0.5,
        )
    assert isinstance(circle,DataFrame)
    assert not circle.empty


def test_gmwcodes_from_rectangle(rect):

    rectangle = _brorest.get_bro_gmwcodes_from_area(
        xmin=rect['xmin'],
        xmax=rect['xmax'],
        ymin=rect['ymin'],
        ymax=rect['ymax'],
        )
    assert isinstance(rectangle, DataFrame)
    assert not rectangle.empty

