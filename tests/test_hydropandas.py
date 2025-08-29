
import pytest
import numpy as np
from pandas import DataFrame
import pandas as pd
import hydropandas as hpd

from acequia import GwSeries
from acequia._read.hydropandas import HydropandasGroundwaterObs
from acequia._read.hydropandas import HydropandasObsCollection


@pytest.fixture
def obscollection():
    #obscoll = pd.read_pickle(r'.\data\hydropandas\hydropandas_gwcollection.pkl')
    xmin=130250
    xmax=131500
    ymin=588750
    ymax=589750
    obscol = hpd.read_lizard(extent=[xmin, xmax, ymin, ymax])    
    return obscol


@pytest.fixture
def obs(obscollection):
    #obs = pd.read_pickle(r'.\data\hydropandas\hydropandas_gwobservations.pkl')    
    obs = obscollection.obs.iloc[0]
    return obs


# test gwobs
# ----------

def test_obs(obs):
    hpo = HydropandasGroundwaterObs(obs)
    assert not hpo._obs.empty
    

def test_obs_getgwseries(obs):
    hpo = HydropandasGroundwaterObs(obs)
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
    assert isinstance(obc.loclist, np.ndarray)
    assert not len(obc.loclist)==0

def test_getseries(obscollection):
    obc = HydropandasObsCollection(obscollection)
    gw = obc.get_gwseries(obc.names[0])
    assert isinstance(gw, GwSeries)

def test_iteritems(obscollection):
    obc = HydropandasObsCollection(obscollection)
    for gw in obc.iteritems():
        assert isinstance(gw, GwSeries)

def test_iterate(obscollection):
    obc = HydropandasObsCollection(obscollection)
    for gw in obc:
        assert isinstance(gw, GwSeries)

