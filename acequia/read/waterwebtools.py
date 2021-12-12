"""This module contains tools for working with the WaterWeb class"""

from pathlib import Path
import warnings
import pandas as pd
from .waterweb import WaterWeb

def measurement_types(fdir,zeros=True,rowsum=True,colsum=True):
    """
    Return table of measurement types for mutiple networks

    Parameters
    ----------
    fdir : str
        valid directory path with WaterWeb csv sourcefiles
    zeros : bool, default True
        show zeros in table
    rowsum : bool, default True
        add column with row totals
    colsum : bool, default True
        add row with column totals

    Returns
    -------
    pd.DataFrame
        table of measurement type counts for all networks
    """

    if not Path(fdir).exists:
        raise ValueError(f'Directory {fdir} does not exist.')

    # list of series with counts for each network file
    pathlist = Path(fdir).glob('**/*')
    filelist = [x for x in pathlist if x.is_file()]

    counts_list = []
    for fname in filelist:
        wwn = WaterWeb.from_csv(fname)
        counts_list.append(wwn.type_counts())

    # table of measurment type by network names
    tbl_list = [pd.DataFrame(sr).T for sr in counts_list]
    tbl = pd.concat(tbl_list).fillna(0)
    for col in tbl.columns:
        tbl[col] = tbl[col].astype(int)

    # sort column names
    if not set(tbl.columns) - set(wwn._measurement_types):
        tbl = tbl.reindex(wwn._measurement_types, axis=1)
    else: #tbl2.columns contains names not in _measurement_types
        warnings.warn('Non-standard measurement types found.')
        tbl = tbl.reindex(sorted(tbl.columns), axis=1)

    if rowsum==True:
        tbl['total'] = tbl.sum(axis=1)

    if colsum==True:
        tbl.loc['total',:] = tbl.sum()

    if not zeros: # show no zeros but empty string
        tbl = tbl.copy()
        for col in tbl.columns:
            tbl[col] = tbl[col].astype(str)
        tbl = tbl.replace('0','')

    return tbl
