
import pytest

from acequia import CrdCon, convert_RDtoWGS84, convert_WGS84toRD

@pytest.fixture
def xRD():
    return CrdCon.Towers['Martinitoren']['xRD']

@pytest.fixture
def yRD():
    return CrdCon.Towers['Martinitoren']['yRD']

@pytest.fixture
def lat():
    return CrdCon.Towers['Martinitoren']['Lat_WGS84']

@pytest.fixture
def lon():
    return CrdCon.Towers['Martinitoren']['Lon_WGS84']


def test_convert_RDtoWGS84(xRD, yRD, lat, lon):

    crd = CrdCon()
    res = crd.convert_RDtoWGS84(xRD, yRD, Zone=False)
    assert isinstance(res, dict)
    assert round(res['Lat'], 2) == round(lat,2)
    assert round(res['Lon'], 2) == round(lon,2)


def test_convert_WGS84toRD(xRD, yRD, lat, lon):

    crd = CrdCon()
    res = crd.convert_WGS84toRD(lat, lon)
    assert isinstance(res, dict)
    assert round(res['xRD'], 0) == round(xRD, 0)
    assert round(res['yRD'], 0) == round(yRD, 0)


def test_functions(xRD, yRD, lat, lon):

    lat2, lon2 = convert_RDtoWGS84(xRD, yRD)
    xRD2, yRD2 = convert_WGS84toRD(lat2, lon2)
    assert isinstance(convert_RDtoWGS84(xRD2, yRD2), tuple)
    assert isinstance(convert_WGS84toRD(lat2, lon2), tuple)
    assert round(xRD, 2) == round(xRD2, 2)
    assert round(yRD, 2) == round(yRD2, 2)
    assert round(lat, 2) == round(lat2, 2)
    assert round(lon, 2) == round(lon2, 2)
