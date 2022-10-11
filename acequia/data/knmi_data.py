"""
Datasets included with Acequia.
    
"""

import pkg_resources
import pandas as pd


def knmi_prc_coords():
    """Return coordinates of KNMI precipitation stations."""

    # This is a stream-like object. If you want the actual info, call
    # stream.read()
    fpath = 'knmi_precipitation_coords.csv'
    stream = pkg_resources.resource_stream(__name__, fpath)
    stn =  pd.read_csv(stream, encoding='latin-1')
    stn = stn.set_index('stn_nr')
    return stn
