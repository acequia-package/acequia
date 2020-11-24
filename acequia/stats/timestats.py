
from collections import OrderedDict
import warnings
import pandas as pd
from pandas import DataFrame, Series
import acequia as aq 

class TimeStats:
    """ Return descriptive statistics of time series"""

    def __init__(self, ts, name=None):
        """
        Parameters
        ----------
        ts : pd.Series, aq.GwSeries
            timeseries with groundwater head measurments

        """

        self.ts = ts
        self.name = name

        """
        if isinstance(self.ts,aq.GwSeries):
            #if self.name is None:
            #    self.name = self.ts.name()
        """

        if isinstance(self.ts,pd.Series):
            if self.name is None: 
                self.name = self.ts.name

        if self.name is None: 
            self.name = 'series'


    def _heads(self,ref='datum'):
        """Return timeseries with measured heads"""
        if isinstance(self.ts,aq.GwSeries):
            heads = self.ts.heads(ref=ref)
        if isinstance(self.ts,pd.Series):
            msg = f'heads series is type pd.Series, ref={ref} is ignored'
            warnings.warn(msg)
            heads = self.ts
        return heads


    def stats(self, ref='datum'):
        """Return time series desciptive statistics

        Parameters
        ----------
        ref : str, ['datum','surface']
            reference level for measurements
        """

        heads = self._heads(ref=ref)
        idx = self.name
        stats = DataFrame(index=[idx])

        stats['firstdate'] = heads.index.min().date()
        stats['lastdate'] = heads.index.max().date()
        stats['minyear'] = heads.index.min().year
        stats['maxyear'] = heads.index.max().year
        stats['yearspan'] = stats['maxyear']-stats['minyear']+1
        stats['nyears'] = len(set(heads.index.year))
        stats['mean'] = round(heads.mean(),2)
        stats['median'] = round(heads.median(),2)

        q05 = heads.quantile(q=0.05)
        q95 = heads.quantile(q=0.95)
        stats['q05'] = round(q05,2)
        stats['q95'] = round(q95,2)
        stats['delta'] = round(q95-q05,2)

        return stats

