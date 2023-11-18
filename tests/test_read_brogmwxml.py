
import pytest
from pandas import Series, DataFrame
from pandas import DataFrame
from acequia import BroGmwXml

@pytest.fixture
def gmwid():
    return 'GMW000000020136'

@pytest.fixture
def gmwserv(gmwid):
    gmw = BroGmwXml.from_server(gmwid=gmwid, description='Testing BroGmwXml.')
    return gmw

@pytest.fixture
def gmwxml():
    xmlpath = r'.\data\bro\Grondwatermonitoringput BRO\GMW000000020136_IMBRO.xml'

    gmw = BroGmwXml.from_xml(xmlpath)
    return gmw

# test constructors
# -----------------

def test_from_server(gmwserv):
    assert isinstance(gmwserv, BroGmwXml)

def test_from_file(gmwxml):
    assert isinstance(gmwxml, BroGmwXml)

def test_bad_file():
    # give GLD file instead of GMW file by mistake
    xmlpath = r'.\data\bro\Grondwaterstandonderzoek BRO\GMW000000020136_IMBRO.xml'
    with pytest.raises(ValueError):
        gmw = BroGmwXml.from_xml(xmlpath)

# test methods
# ------------

@pytest.mark.parametrize('gmw', [gmwserv, gmwxml])
def test_events(gmw, request):
    gmw = request.getfixturevalue(gmw.__name__)
    assert isinstance(gmw.events, DataFrame)

@pytest.mark.parametrize('gmw', [gmwserv, gmwxml])
def test_tubeprops(gmw, request):
    gmw = request.getfixturevalue(gmw.__name__)
    df = gmw.tubeprops
    assert isinstance(df, DataFrame)
    assert not df.empty

@pytest.mark.parametrize('gmw', [gmwserv, gmwxml])
def test_wellprops(gmw, request):
    gmw = request.getfixturevalue(gmw.__name__)
    sr = gmw.wellprops
    assert isinstance(sr, Series)
    assert not sr.empty

@pytest.mark.parametrize('gmw', [gmwserv, gmwxml])
def test_wellprops(gmw, request):
    gmw = request.getfixturevalue(gmw.__name__)
    assert isinstance(gmw.gmwid, str)
