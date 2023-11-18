
import pytest
from pandas import Series, DataFrame
from acequia import BroGwSeries
from acequia import _brorest as brorest

@pytest.fixture
def brosrest():
    """Get BroGwSeries object from REST service."""
    gmwid = 'GMW000000020136'
    welltubes = brorest.get_welltubes(gmwid)
    tube = welltubes.index[0]
    bros = BroGwSeries.from_server(gmwid=gmwid, tube=tube)
    return bros

@pytest.fixture
def brosfile():
    """Get BroGwSeries object from XML files."""
    gmwfile = 'GMW000000020138_IMBRO.xml'
    gldfile = 'GLD000000009095_IMBRO_A.xml'
    
    gmwpath = f'.\\data\\bro\\Grondwatermonitoringput BRO\\{gmwfile}'
    gldpath = f'.\\data\\bro\\Grondwaterstandonderzoek BRO\\{gldfile}'
    
    bros = BroGwSeries.from_files(gmwpath=gmwpath, gldpath=gldpath)
    return bros


# test main properties/methods

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_wellprops(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    sr = bros.wellprops
    assert isinstance(sr, Series)
    assert not sr.empty

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_tubeprops(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    sr = bros.tubeprops
    assert isinstance(sr, Series)
    assert not sr.empty

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_gwseries(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    gw = bros.gwseries
    mystring = gw.name()
    assert isinstance(mystring, str)
    assert not len(mystring)==0

# test string properties

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_gldid(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.gldid
    assert isinstance(mystring, str)
    assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_gmwid(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.gmwid
    assert isinstance(mystring, str)
    assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_nitgcode(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.nitgcode
    assert isinstance(mystring, str)
    ## assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_ownerid(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.ownerid
    assert isinstance(mystring, str)
    assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_seriesname(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.seriesname
    assert isinstance(mystring, str)
    assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_tubeid(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.tubeid
    assert isinstance(mystring, str)
    assert not len(mystring)==0

@pytest.mark.parametrize('bros', [brosrest, brosfile])
def test_wellcode(bros, request):
    bros = request.getfixturevalue(bros.__name__)
    mystring = bros.wellcode
    assert isinstance(mystring, str)
    assert not len(mystring)==0
