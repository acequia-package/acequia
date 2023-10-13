

import pytest
from pandas import Series, DataFrame
from acequia import brorest
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

    circle = brorest.get_area_wellprops(lowerleft=None,upperright=None,
        center=(52.349968,7.064451),radius=0.5)
    assert isinstance(circle,DataFrame)
    assert not circle.empty

    rectangle = brorest.get_area_wellprops(lowerleft=(52.340333,6.865430),
        upperright=(52.347915,6.888625),center=None,radius=None)
    assert isinstance(rectangle,DataFrame)
    assert not rectangle.empty

def test_singlewellprops(gmwid):
    props = brorest.get_wellprops(gmwid)
    assert isinstance(props, BroGmwXml)
    assert not props.tubeprops.empty
    assert not props.wellprops.empty

def test_getwelltubes(gmwid):
    tubes = brorest.get_welltubes(gmwid)
    assert isinstance(tubes, DataFrame)
    assert not tubes.empty

def test_getwellcode(gmwid):
    wellcode = brorest.get_wellcode(gmwid)
    assert isinstance(wellcode, str)
    assert len(wellcode)!=0

def test_getlevels(brogld):
    levels = brorest.get_levels(brogld=brogld) #'GLD000000010138') #'GLD000000009881')
    assert isinstance(levels,BroGldXml)
    assert not levels.heads.empty

def test_getgmwcodes(broinstantie):
    gmwlist = brorest.get_gmw_codes('51048329')
    assert isinstance(gmwlist,list)
    assert len(gmwlist)!=0

def test_getgldcodes(broinstantie):
    gldlist = brorest.get_gld_codes('51048329')
    assert isinstance(gldlist,list)
    assert len(gldlist)!=0
