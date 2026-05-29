

from importlib import resources as _resources
import pandas as _pd

from . import _bro_data

def bro_instanties():
    """Names of bronhouders by ID as given at
    https://basisregistratieondergrond.nl/service-contact/formulieren/aangemeld-bro/"""

    srcfile = (_resources.files(_bro_data) / 'broinstanties.csv')
    df = _pd.read_csv(srcfile)
    return df.set_index('broid', verify_integrity=True).squeeze()
