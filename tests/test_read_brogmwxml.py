
import pytest
from pandas import Series, DataFrame
from pandas import DataFrame
from acequia import BroGmwXml

@pytest.fixture
def gmw():
    xmlpath = r'.\data\bro\Grondwaterstandonderzoek BRO\GMW000000041126_IMBRO_A.xml'
    return BroGmwXml.from_file(xmlpath)

