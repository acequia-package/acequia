
import pytest
import collections
from pandas import DataFrame
from acequia import GpxTree

fpath = r'.\data\gpx\BrittanyJura\Ouistreham_Caen.gpx'

# test constructors
def test_init_raises_error_with_None_as_parameter():
    with pytest.raises(AttributeError):
        GpxTree(None)

def test_classmethod_read_from_file():
    gpxtree = GpxTree.from_file(fpath)
    assert isinstance(gpxtree,GpxTree)

@pytest.fixture
def gpxtree():
    """Return GpxTree instance with tree from gpx file"""
    return GpxTree.from_file(fpath)

# test private methods
def test__get_meta(gpxtree):
    result = gpxtree._get_meta()
    assert isinstance(result,collections.abc.Mapping)

def test__get_waypoints(gpxtree):
    result = gpxtree._get_waypoints()
    assert isinstance(result,DataFrame)
    assert not result.empty

def test__get_trackpoints(gpxtree):
    result = gpxtree._get_trackpoints()
    assert isinstance(result,DataFrame)
    assert not result.empty

# test properties
def test_meta(gpxtree):
    assert isinstance(gpxtree.meta, collections.abc.Mapping)

def test_bounds(gpxtree):
    assert isinstance(gpxtree.bounds, collections.abc.Mapping)

def test_trackpoints(gpxtree):
    assert isinstance(gpxtree.trackpoints,DataFrame)
    assert not gpxtree.trackpoints.empty

def test_waypoints(gpxtree):
    assert isinstance(gpxtree.waypoints,DataFrame)
    assert not gpxtree.waypoints.empty

def test_contents(gpxtree):
    assert isinstance((list(gpxtree.contents)),list)

