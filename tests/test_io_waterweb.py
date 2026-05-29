
import pytest
import pandas as pd
from geopandas import GeoDataFrame
from acequia.io._waterwebtools import measurement_types
from acequia.io import WaterWeb
from acequia import GwSeries

wwdir = r'.\data\waterweb\\'
#fpath = f'{wwdir}waterweb_csv_kolommen.csv'
#fpath2 = f'{wwdir}waterweb_csv_2025.csv'
fpath = f'{wwdir}waterweb_test.csv'
networkname = 'Waterweb testfile'

# test class WaterWeb

@pytest.fixture
def wwn():
    return WaterWeb.from_csv(fpath=fpath, network=networkname)

#@pytest.fixture
#def wwn_old():
#    return WaterWeb.from_csv(fpath=fpath, network=networkname)

#@pytest.fixture
#def wwn_2025():
#    return WaterWeb.from_csv(fpath=fpath2, network=None)

# test properties

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_measurement_types(wwn):
    assert isinstance(wwn.measurement_types, pd.Series)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_networkname(wwn):
    assert isinstance(wwn.networkname, str)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_networkname_setter(wwn):
    original_name = wwn.networkname
    wwn.networkname = 'different name'
    assert isinstance(wwn.networkname,str)
    assert wwn.networkname!=original_name

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_series_properties(wwn):
    gdf = wwn.series_properties
    assert isinstance(gdf,GeoDataFrame)
    assert not gdf.empty

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_location_properties(wwn):
    gdf = wwn.location_properties
    assert isinstance(gdf, GeoDataFrame)
    assert not gdf.empty

# test methods

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_measurement_type(wwn):
    for name in wwn.names:
        srtype = wwn.get_measurement_type(name)
        assert isinstance(srtype,str)
        assert srtype in wwn.MEASUREMENT_TYPES

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_locname(wwn):
    assert isinstance(wwn.get_locname(wwn.names[0]),str)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_filname(wwn):
    assert isinstance(wwn.get_filname(wwn.names[0]),str)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_locprops(wwn):
    locprops = wwn.get_locprops(wwn.names[0])
    assert isinstance(locprops, pd.Series)
    assert locprops.empty is False

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_tubeprops(wwn):
    tubeprops = wwn.get_tubeprops(wwn.names[0])
    assert isinstance(tubeprops,pd.DataFrame)
    assert tubeprops.empty is False

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_levels(wwn):

    for ref in ['mp','datum','surface']:
        levels = wwn.get_levels(wwn.names[0], ref=ref)
        assert isinstance(levels,pd.Series)
        assert levels.empty is False
        assert pd.to_numeric(levels, errors='coerce').notnull().all()

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_gwseries(wwn):
    srname = wwn.names[0]
    gw = wwn.get_gwseries(srname)
    assert isinstance(gw.heads(),pd.Series)
    assert gw.heads().empty is False

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_to_kml(wwn):
    outpath = f'.\\output\\kml\\{wwn.networkname}.kml'
    wwn.to_kml(outpath)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_iteritems(wwn):
    for gw in wwn.iteritems():
        assert isinstance(gw,GwSeries)

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_is_suncode(wwn):
  assert all([wwn.is_suncode(name) for name in wwn.names])
  
  # test some possible inputs
  assert wwn.is_suncode('12345678B001A')
  assert wwn.is_suncode('12345678B001')
  assert not wwn.is_suncode('invalidname')

#@pytest.mark.parametrize('wwn', [wwn_old, wwn_2025,])
def test_get_series_shortname(wwn):
    for srname in wwn.names:
        # as_location=False
        shortname = wwn.get_series_shortname(srname, as_location=False)
        assert isinstance(shortname, str)
        # as_location=True
        shortname = wwn.get_series_shortname(srname, as_location=True)
        assert isinstance(shortname, str)

# test custom functions in module waterwebtools

"""
def test_measurement_types():
    tbl = measurement_types(wwdir)
    assert isinstance(tbl,pd.DataFrame)
    assert tbl.empty is False
"""
