
import pytest
from pandas import DataFrame
import pandas as pd

from acequia import GwSeries
from acequia._read.hydropandas import HydropandasGroundwaterObservations
from acequia._read.hydropandas import HydropandasObsCollection


@pytest.fixture
def obs():
    obs = pd.read_pickle(r'.\data\hydropandas\hydropandas_gwobservations.pkl')
    return obs

@pytest.fixture
def obscollection():
    obscoll = pd.read_pickle(r'.\data\hydropandas\hydropandas_gwcollection.pkl')
    return obscoll

# test gwobs
# ----------

def test_obs(obs):
    hpo = HydropandasGroundwaterObservations(obs)
    assert not hpo._obs.empty
    

def test_obs_getgwseries(obs):
    hpo = HydropandasGroundwaterObservations(obs)
    gw = hpo.get_gwseries()
    assert isinstance(gw, GwSeries)

# test obscollection
# ------------------

def test_obscol(obscollection):
    obc = HydropandasObsCollection(obscollection)
    isinstance(obc, HydropandasObsCollection)

def test_obscol_empty(obscollection):
    obc = HydropandasObsCollection(obscollection)
    assert not obc.empty

def test_obscol_loclist(obscollection):
    obc = HydropandasObsCollection(obscollection)
    assert isinstance(obc.loclist, list)
    assert not len(obc.loclist)==0

def test_obscol_loclist(obscollection):
    obc = HydropandasObsCollection(obscollection)
    assert isinstance(obc.names, list)
    assert not len(obc.names)==0

def test_getseries(obscollection):
    obc = HydropandasObsCollection(obscollection)
    gw = obc.get_gwseries(obc.names[0])
    assert isinstance(gw, GwSeries)

def test_iterate(obscollection):
    obc = HydropandasObsCollection(obscollection)
    for gw in obc:
        assert isinstance(gw, GwSeries)

def test_iteritems(obscollection):
    obc = HydropandasObsCollection(obscollection)
    for gw in obc.iteritems():
        assert isinstance(gw, GwSeries)

