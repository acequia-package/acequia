
import pytest
import collections
from pandas import DataFrame
from acequia import GpxTree, GpxTracklog

fpath = r'.\data\gpx\BrittanyJura\Ouistreham_Caen.gpx'

def test_from_file():
    gpx = GpxTracklog.from_file(fpath)
    assert isinstance(gpx, GpxTracklog)

def test_init():

    gpxtree = GpxTree.from_file(fpath)

    gpx = GpxTracklog(gpxtree=gpxtree, filepath=fpath)
    assert isinstance(gpx, GpxTracklog)

    # forget to supply GpxTree instance
    with pytest.raises(TypeError):
        GpxTracklog()

    # supply invalid filepath
    with pytest.raises(ValueError):
        gpx = GpxTracklog(gpxtree=gpxtree, filepath="invalidpath")


@pytest.fixture
def gpx():
    """Return GpxTracklog instance."""
    return GpxTracklog.from_file(fpath=fpath)

def test_trackpoints(gpx):
    df = gpx.trackpoints
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_tracks(gpx):
    df = gpx.tracks
    assert isinstance(df, DataFrame)
    assert not df.empty

def test_waypoints(gpx):
    df = gpx.waypoints
    assert isinstance(df, DataFrame)
    assert not df.empty

