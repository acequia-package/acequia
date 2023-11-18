
import pytest
from pandas import Series, DataFrame
from acequia import BroGwSeries

@pytest.fixture
def gmwid():
    return 'GMW000000041145'

@pytest.fixture
def brogld():
    return 'GLD000000010138'


