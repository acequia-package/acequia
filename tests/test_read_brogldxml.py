
import pytest
import lxml.etree as ET
from pandas import Series, DataFrame
from pandas import DataFrame
from geopandas import GeoDataFrame
from acequia import BroGldXml
from acequia import _brorest

@pytest.fixture
def filegld():
    xmlpath = r'.\data\bro\Grondwaterstandonderzoek BRO\GLD000000009526_IMBRO_A.xml'
    return BroGldXml.from_xml(xmlpath)

@pytest.fixture
def restgld():
    return BroGldXml.from_server('GLD000000009526', 
        startdate='1900-01-01', enddate='2022-12-31', reference='Test')

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_gldprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    sr = gld.gldprops
    assert isinstance(sr,Series)
    assert not sr.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_obs(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    df = gld.obs
    assert isinstance(df,DataFrame)
    assert not df.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_obsprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    df = gld.obsprops
    assert isinstance(df,DataFrame)
    assert not df.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_procesprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    df = gld.procesprops
    assert isinstance(df,DataFrame)
    assert not df.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_heads(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    sr = gld.heads
    assert isinstance(sr, Series)
    assert not gld.heads.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_isgld(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert gld.is_gld

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_gldid(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    mystr = gld.gldid
    assert isinstance(mystr, str)

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_gmwid(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    mystr = gld.gmwid
    assert isinstance(mystr, str)

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_tubeid(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    mystr = gld.tubeid
    assert isinstance(mystr, str)

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_timeseriescounts(gld, request):
    gld = request.getfixturevalue(gld.__name__)
    sr = gld.timeseriescounts
    assert isinstance(sr,Series)
    assert not sr.empty


