
import pytest
import pandas as pd
from geopandas import GeoDataFrame
from acequia import measurement_types
from acequia import WaterWeb

fpath = r'.\data\waterweb\grolloer koelanden.csv'
networkname = 'grolloer koelanden'
wwdir = r'.\data\waterweb\\'

# test class WaterWeb

@pytest.fixture
def wwn():
    return WaterWeb.from_csv(fpath=fpath,network=networkname)

def test_init():
    wwninit = WaterWeb(fpath=fpath,network=networkname)
    assert len(wwninit.srnames)==0

def test_from_csv(wwn):
    assert len(wwn.srnames)!=0

def test_get_type(wwn):
    srtype = wwn.get_type(wwn.srnames[0])
    assert isinstance(srtype,str)
    assert srtype in wwn.MEASUREMENT_TYPES

def test_measurement_types(wwn):
    assert isinstance(wwn.measurement_types,pd.Series)

def test_get_locname(wwn):
    assert isinstance(wwn.get_locname(wwn.srnames[0]),str)

def test_get_filname(wwn):
    assert isinstance(wwn.get_filname(wwn.srnames[0]),str)

def test_networkname_setter(wwn):
    original_name = wwn.networkname
    wwn.networkname = 'different name'
    assert isinstance(wwn.networkname,str)
    assert wwn.networkname!=original_name

def test_get_locprops(wwn):
    locprops = wwn.get_locprops(wwn.srnames[0])
    assert isinstance(locprops,pd.Series)
    assert locprops.empty is False

def test_get_tubeprops(wwn):
    tubeprops = wwn.get_tubeprops(wwn.srnames[0])
    assert isinstance(tubeprops,pd.DataFrame)
    assert tubeprops.empty is False

def test_get_levels(wwn):
    levels = wwn.get_levels(wwn.srnames[0])
    assert isinstance(levels,pd.Series)
    assert levels.empty is False

def test_get_gwseries(wwn):
    srname = wwn.srnames[0]
    gw = wwn.get_gwseries(srname)
    assert isinstance(gw.heads(),pd.Series)
    assert gw.heads().empty is False

def test_locations(wwn):
    locs = wwn.locations
    assert isinstance(locs,GeoDataFrame)
    assert not locs.empty

def test_to_kml(wwn):
    outpath = f'.\\output\\kml\\{wwn.networkname}.kml'
    wwn.to_kml(outpath)


# test custom functions in module waterwebtools

def test_measurement_types():
    tbl = measurement_types(wwdir)
    assert isinstance(tbl,pd.DataFrame)
    assert tbl.empty is False
