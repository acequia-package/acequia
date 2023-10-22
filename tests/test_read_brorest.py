

import pytest
from pandas import Series, DataFrame
from xml.etree.ElementTree import ElementTree

from acequia import _brorest
from acequia import BroGmwXml, BroGldXml


@pytest.fixture
def gmwid():
    return 'GMW000000041145'

@pytest.fixture
def brogld():
    return 'GLD000000010138'
    
@pytest.fixture
def broinstantie():
    return '51048329'

def test_getareawellprops():

    circle = _brorest.get_area_wellprops(lowerleft=None,upperright=None,
        center=(52.349968,7.064451),radius=0.5)
    assert isinstance(circle,DataFrame)
    assert not circle.empty

    rectangle = _brorest.get_area_wellprops(lowerleft=(52.340333,6.865430),
        upperright=(52.347915,6.888625),center=None,radius=None)
    assert isinstance(rectangle,DataFrame)
    assert not rectangle.empty

def test_getwelltubes(gmwid):
    tubes = _brorest.get_welltubes(gmwid)
    assert isinstance(tubes, DataFrame)
    assert not tubes.empty

def test_getwellcode(gmwid):
    wellcode = _brorest.get_wellcode(gmwid)
    assert isinstance(wellcode, str)
    assert len(wellcode)!=0

def test_getgmwcodes(broinstantie):
    gmwlist = _brorest.get_gmw_codes('51048329')
    assert isinstance(gmwlist,list)
    assert len(gmwlist)!=0

def test_getgldcodes(broinstantie):
    gldlist = _brorest.get_gld_codes('51048329')
    assert isinstance(gldlist,list)
    assert len(gldlist)!=0

def test_getwellprops(gmwid):
    props = _brorest.get_wellprops(gmwid)
    assert isinstance(props, ElementTree)
    assert len(list(props.iter()))!=0

def test_getlevels(brogld):
    levels = _brorest.get_levels(brogld=brogld) #'GLD000000010138') #'GLD000000009881')
    assert isinstance(levels, ElementTree)
    assert len(list(levels.iter()))!=0
