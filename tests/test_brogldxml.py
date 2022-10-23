
import pytest
from pandas import Series, DataFrame
from pandas import DataFrame
from geopandas import GeoDataFrame
from acequia import BroGldXml



@pytest.fixture
def gld():
    xmlpath = r'.\data\bro\Grondwaterstandonderzoek BRO\GLD000000009526_IMBRO_A.xml'
    return BroGldXml.from_file(xmlpath)

def test_property_gldprops(gld):
    assert isinstance(gld.gldprops,Series)
    assert not gld.gldprops.empty

def test_property_obs(gld):
    assert isinstance(gld.obs,DataFrame)
    assert not gld.obs.empty

def test_property_obsprops(gld):
    assert isinstance(gld.obsprops,DataFrame)
    assert not gld.obsprops.empty

def test_property_procesprops(gld):
    assert isinstance(gld.procesprops,DataFrame)
    assert not gld.procesprops.empty

def test_property_heads(gld):
    assert isinstance(gld.heads,Series)
    assert not gld.heads.empty
