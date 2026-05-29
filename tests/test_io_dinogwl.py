


import pytest
from acequia import GwSeries
from acequia.io import BroDataDinoGwl, BroDataDinoGwlCollection

@pytest.fixture
def dn():
    return BroDataDinoGwl.from_nitgcode("B13D0169", 1)

# test BroDataDinoGwl
# -------------------

def test_download(dn):
    assert isinstance(dn, BroDataDinoGwl)

def test_gwseries(dn):
    assert isinstance(dn.gwseries(), GwSeries)


# test BroDataDinoGwlCollection
# -----------------------------

@pytest.fixture
def collection():
    return BroDataDinoGwlCollection.from_rectangle(
        xmin=271500, xmax=272000, ymin=551240, ymax=551600)

def test_download(collection):
    assert isinstance(collection, BroDataDinoGwlCollection)

def test_items(collection):
    assert isinstance(collection.items(), list)
    assert collection.items()

def test_gwseries(collection):
    loc, tube = collection.items()[0]
    gw = collection.gwseries(loc, tube)
    assert isinstance(gw, GwSeries)
    assert not gw.empty

def test_iteritems(collection):
    for gw in collection.iteritems():
        assert isinstance(gw, GwSeries)
        assert not gw.empty

def test_empty(collection):
    assert not collection.empty

    # create empty collection
    xmin=271500
    xmax=xmin+1
    ymin=551240
    ymax=ymin+1
    col=BroDataDinoGwlCollection.from_rectangle(
        xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    assert col.empty
    