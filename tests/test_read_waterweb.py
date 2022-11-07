
import pytest
import pandas as pd
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

def test_measurement_kind(wwn):
    srtype = wwn.measurement_kind(wwn.srnames[0])
    assert isinstance(srtype,str)
    assert srtype in wwn._measurement_types

def test_type_counts(wwn):
    assert isinstance(wwn.type_counts,pd.Series)

def test_locname(wwn):
    assert isinstance(wwn.locname(wwn.srnames[0]),str)

def test_filname(wwn):
    assert isinstance(wwn.filname(wwn.srnames[0]),str)

def test_networkname_setter(wwn):
    original_name = wwn.networkname
    wwn.networkname = 'different name'
    assert isinstance(wwn.networkname,str)
    assert wwn.networkname!=original_name

def test_locprops(wwn):
    locprops = wwn.locprops(wwn.srnames[0])
    assert isinstance(locprops,pd.Series)
    assert locprops.empty is False

def test_tubeprops(wwn):
    tubeprops = wwn.tubeprops(wwn.srnames[0])
    assert isinstance(tubeprops,pd.DataFrame)
    assert tubeprops.empty is False

def test_levels(wwn):
    levels = wwn.levels(wwn.srnames[0])
    assert isinstance(levels,pd.Series)
    assert levels.empty is False

def test_gwseries(wwn):
    srname = wwn.srnames[0]
    gw = wwn.gwseries(srname)
    assert isinstance(gw.heads(),pd.Series)
    assert gw.heads().empty is False

# test custom functions in module waterwebtools

def test_measurement_types():
    tbl = measurement_types(wwdir)
    assert isinstance(tbl,pd.DataFrame)
    assert tbl.empty is False
