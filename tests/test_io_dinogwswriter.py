
import pytest
from pandas import Series, DataFrame
import pandas as pd
from acequia import GwSeries
from acequia.io import DinoGwsWriter
import acequia as aq

jsonpath = r".\data\json\GMW000000020076_1.json"
outdir = r'.\output\dinocsv\\'

@pytest.fixture
def gw():
    return GwSeries.from_json(r'.\data\json\GMW000000041484_1.json')
    #return GwSeries.from_json(jsonpath)


def test_init(gw):
    writer = DinoGwsWriter(gw)
    assert isinstance(writer, DinoGwsWriter)
    assert isinstance(writer.save(outdir), list)

    # with empty gwseries
    writer = DinoGwsWriter(GwSeries())
    assert isinstance(writer, DinoGwsWriter)
    assert writer.save(outdir) is None


def test_locname(gw):
    writer = DinoGwsWriter(gw)
    locname = writer.locname()
    assert isinstance(locname, str)
    assert not pd.isnull(locname)

    writer = DinoGwsWriter(GwSeries())
    locname = writer.locname()
    assert not isinstance(locname, str)
    assert pd.isnull(locname)


def test_header(gw):
    writer = DinoGwsWriter(gw)
    df = writer.header()
    assert isinstance(df, DataFrame)
    assert not all(df.isnull().all())

    # with empty gwseries
    writer = DinoGwsWriter(GwSeries())
    df = writer.header()
    assert isinstance(df, DataFrame)
    assert all(df.isnull().all())


def test_obs(gw):
    writer = DinoGwsWriter(gw)
    df = writer.obs()
    assert isinstance(df, DataFrame)
    assert not all(df.isnull().all())

    # with empty gwseries
    writer = DinoGwsWriter(GwSeries())
    df = writer.obs()
    assert isinstance(df, DataFrame)
    assert all(df.isnull().all())


def test_filelines(gw):
    writer = DinoGwsWriter(gw)
    lines = writer.filelines()
    assert isinstance(lines, list)
    assert lines # not empty

    # with empty gwseries
    writer = DinoGwsWriter(GwSeries())
    lines = writer.filelines()
    assert isinstance(lines, list)
    assert lines # not empty


def test_tube(gw):
    writer = DinoGwsWriter(gw)
    tube = writer.tube()
    assert isinstance(tube, int)

    writer = DinoGwsWriter(GwSeries())
    tube = writer.tube()
    assert pd.isnull(tube)
