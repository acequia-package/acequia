
import pytest
import lxml.etree as ET
from pandas import Series, DataFrame
from pandas import DataFrame
from geopandas import GeoDataFrame
from acequia import BroGldXml


@pytest.fixture
def filegld():
    xmlpath = r'.\data\bro\Grondwaterstandonderzoek BRO\GLD000000009526_IMBRO_A.xml'
    return BroGldXml.from_file(xmlpath)

@pytest.fixture
def restgld():
    # parse xml file that contains an xml from the BRO REST service
    xmlpath = r'.\data\bro\RESTXML\GLD000000009526.xml'  #GLD000000010071.xml'
    tree = ET.parse(xmlpath)
    return BroGldXml.from_rest(tree)

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_gldprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert isinstance(gld.gldprops,Series)
    assert not gld.gldprops.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_obs(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert isinstance(gld.obs,DataFrame)
    assert not gld.obs.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_obsprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert isinstance(gld.obsprops,DataFrame)
    assert not gld.obsprops.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_procesprops(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert isinstance(gld.procesprops,DataFrame)
    assert not gld.procesprops.empty

@pytest.mark.parametrize('gld', [filegld, restgld])
def test_property_heads(gld,request):
    gld = request.getfixturevalue(gld.__name__)
    assert isinstance(gld.heads,Series)
    assert not gld.heads.empty

