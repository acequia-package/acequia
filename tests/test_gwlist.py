

import pytest
import acequia as aq

dinodir = '.\\data\\dinogws\\'
hymonpath = '.\\data\\hymon\hydromonitor_testdata.csv'

def test_GwList_init():

    with pytest.raises(ValueError):
        # arguments srcdir and srcfile both missing
        gwl = aq.GwList()

    with pytest.raises(ValueError):
        # invalid srctype
        gwl = aq.GwList(srcdir=dinodir,srctype='dummy')
    
    with pytest.raises(ValueError):
        # srcdir does not exist
        gwl = aq.GwList(srcdir='dummy')

