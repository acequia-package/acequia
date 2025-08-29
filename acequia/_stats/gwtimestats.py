
from collections import OrderedDict
import warnings
import numpy as np
from pandas import DataFrame, Series
import pandas as pd

#from .._core import gwseries
from .utils import maxfrq #slice_timeseries # get_ts1428, 

def gwtimestats(ts, ref=None, name=None):
    """Return table of groundwater head time series statistics

    Parameters
    ----------
    ts : pd.Series, aq.GwSeries
        Groundwater head time series
    ref : ['datum','surface','mp'], optional, default 'datum'
        Reference level vfor groundwater heads
    name : str, optional
        Groundwater heads series name

    Returns
    -------
    pd.DataFrame
    """

    gwstats = GwTimeStats(ts, ref=ref, name=name)
    return gwstats.stats()


class GwTimeStats:
    """ Return descriptive statistics of groundwater head time series."""

    def __init__(self, ts=None):
        """
        ts : pd.Series
            Timeseries with groundwater head measurements
            
        """
        if ts is None:
            ts = Series()

        if not isinstance(ts, Series):
            raise ValueError((f'Timeseries must be of type pandas Series. '
                f'Type {ts.__class__.__name__} not supported.'))

        self._ts = ts


    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'


    def __len__(self):
        return len(self._ts)


    @property
    def empty(self):
        if self._ts.empty:
            return True
        return False


    def timestats(self, tmin=None, tmax=None):
        """Return basic desciptive statistics for time series.

        Returns
        -------
        pd.Dataframe

        """
        #ts = slice_timeseries(self._ts, tmin, tmax)
        ts = self._ts

        # create empty series for statistics
        rownames = ['firstdate', 'lastdate', 'minyear', 'maxyear',
            'yearspan', 'nyears', 'maxfrq', 'mean', 'median',
            'q05', 'q95', 'dq0595',]
        stats = Series(index=rownames, name=self._ts.name, dtype='object')

        if not ts.empty:
            q05 = ts.quantile(q=0.05)
            q95 = ts.quantile(q=0.95)
            stats['firstdate'] = ts.index.min().date()
            stats['lastdate'] = ts.index.max().date()
            stats['minyear'] = ts.index.min().year
            stats['maxyear'] = ts.index.max().year
            stats['yearspan'] = stats['maxyear']-stats['minyear']+1
            stats['nyears'] = len(set(ts.index.year))
            stats['maxfrq'] = maxfrq(ts)
            stats['mean'] = round(ts.mean(),2)
            stats['median'] = round(ts.median(),2)
            stats['q05'] = round(q05,2)
            stats['q95'] = round(q95,2)
            stats['dq0595'] = round(q95-q05,2)

        return stats

