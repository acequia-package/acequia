
import pytest
import collections
import numpy as np
from pandas import DataFrame
import pandas as pd
from acequia import GwFiles, GwSeries
import acequia as aq

dinodir = '.\\data\\dinogws\\'
jsondir = '.\\output\\json\\'
csvdir = '.\\output\\csv\\'

@pytest.fixture
def gwf():
    return GwFiles.from_dinocsv(dinodir)


@pytest.fixture
def gwf_dinocsv():
    return GwFiles.from_dinocsv(dinodir)

@pytest.fixture
def gwf_json():
    return GwFiles.from_json(jsondir)

# test constructors
# -----------------

def test_from_dinocsv_with_only_filedir():
    gwf = GwFiles.from_dinocsv(dinodir)
    assert isinstance(gwf.filetable,DataFrame)
    assert not gwf.filetable.empty

def test_from_dinocsv_with_loclist(gwf):
    loclist = gwf.filetable['loc'].values

    gwf2 = GwFiles.from_dinocsv(dinodir,loclist=loclist)
    assert isinstance(gwf2.filetable,DataFrame)
    assert len(gwf2.filetable)!=0

def test_from_json_with_only_filedir():

    gwf = GwFiles.from_json(jsondir)
    assert isinstance(gwf.filetable,DataFrame)
    assert not gwf.filetable.empty

def test_from_json_with_loclist(gwf):

    loclist = gwf.filetable['loc'].values ##[:listlen]

    gwf2 = GwFiles.from_json(jsondir,loclist=loclist)
    assert isinstance(gwf2.filetable,DataFrame)
    assert len(gwf2.filetable)!=0

def test_init_with_invalid_input():

    with pytest.raises(ValueError):
        gwf = GwFiles('A_String')

    with pytest.raises(ValueError):
        badcolumns = DataFrame(columns=['A','B','C',])
        gwf = GwFiles(badcolumns)

# test magic methods
# ------------------

@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_repr(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    assert isinstance(repr(gwf),str)

@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_len(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    assert len(gwf)!=0


# test methods
# ------------

# test property names
@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_names(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    assert isinstance(gwf.names, list)
    assert gwf.names

# test get_gwseries
@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_get_gwseries(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    gwname = gwf.names[0]
    gw = gwf.get_gwseries(gwname)
    assert isinstance(gw,GwSeries)

# test iteritems
@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_iteritems(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    for gw in gwf.iteritems():
        assert isinstance(gw,GwSeries)

# test to_json
@pytest.mark.parametrize('gwf', [gwf_dinocsv, gwf_json])
def test_to_json(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    jsn = gwf.to_json(jsondir)
    assert isinstance(jsn,list)
    assert isinstance(jsn[0],collections.OrderedDict)

# test to_csv
@pytest.mark.parametrize('gwf', [gwf_dinocsv]) #, gwf_json])
def test_to_csv(gwf, request):
    gwf = request.getfixturevalue(gwf.__name__)
    csv = gwf.to_csv(csvdir)
    assert isinstance(csv,list)
    assert isinstance(csv[0],pd.Series)

