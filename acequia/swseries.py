
import collections
import warnings
from pandas import Series, DataFrame
import pandas as pd

from .read.dinosurfacelevel import DinoSurfaceLevel


class SwSeries:
    """ Surface water level series """

    LOCPROPS_NAMES = [
        'locname','alias','xcr','ycr',
        'level_reference','grid_reference']

    LEVELPROPS_NAMES = [
        'level',] #'remark',]

    REMARKPROPS_NAMES = [ 
        'remark']

    MAPPING_DINOLOCPROPS = collections.OrderedDict([
        ('locname','nitgcode'),
        ('alias','alias'),
        ('xcr','xcr'),
        ('ycr','ycr'),
        ('level_reference','reference'),
        ('grid_reference','grid_reference'),
        ])

    MAPPING_DINOLEVELPROPS = collections.OrderedDict([
        ('level','level'),])
        ##('remark','remark'),])

    MAPPING_DINOREMARKPROPS = collections.OrderedDict([
        ('remark','remark'),])


    def __repr__(self):

        name = self.name()
        nlev = len(self.levels())
        return (f'{name} (n={nlev})')


    def __init__(self,levels=None,locprops=None,remarks=None):

        if locprops is None:
            self._locprops = Series(index=self.LOCPROPS_NAMES)
        elif isinstance(locprops,pd.Series):
            self._locprops = locprops
        else:
            raise TypeError(f'Argument locprops is not a pandas Series but '
                f'{type(locprops)}')

        if levels is None:
            self._levels = DataFrame(columns=self.LEVELPROPS_NAMES)
        elif isinstance(levels,pd.DataFrame):
            self._levels = levels
        else:
            raise TypeError(f'Argument levels is not a pandas DataFrame '
                f'but {type(levels)}')

        if remarks is None:
            self._remarks = DataFrame(columns=self.REMARKPROPS_NAMES)
        elif isinstance(remarks,pd.DataFrame):
            self._remarks = remarks
        else:
            raise TypeError(f'Argument remarks is not a pandas DataFrame '
                f'but {type(remarks)}')


    @classmethod
    def from_dinocsv(cls,fpath):
        """Read dinoloket csv file with surface water level measurements
           and return data as SwSeries object"""

        dns = DinoSurfaceLevel(fpath)
        dinolevels = dns.levels()
        dinoprops = dns.locprops()
        dinoremarks = dns.remarks()

        locprops = Series(index=cls.LOCPROPS_NAMES)
        for propname in cls.LOCPROPS_NAMES:
            dnprop = cls.MAPPING_DINOLOCPROPS[propname]
            if dnprop in dinoprops:
                locprops[propname] = dinoprops[dnprop]
            else:
                msg = (f'{dnprop} not in dinocsv locprops names'
                    f'{list(dinoprops.index.values)}')
                warnings.warn(msg)

        levels = DataFrame(columns=cls.LEVELPROPS_NAMES)
        for propname in cls.LEVELPROPS_NAMES:
            dnprop = cls.MAPPING_DINOLEVELPROPS[propname]
            if dnprop in dinolevels:
                levels[propname] = dinolevels[dnprop]
            else:
                msg = (f'{dnprop} not in dinocsv level names'
                    f'{list(dinolevels.index.values)}')
                warnings.warn(msg)

        remarks = DataFrame(columns=cls.REMARKPROPS_NAMES)
        for propname in cls.REMARKPROPS_NAMES:
            dnprop = cls.MAPPING_DINOREMARKPROPS[propname]
            if dnprop in dinoremarks:
                remarks[propname] = dinoremarks[dnprop]
            else:
                msg = (f'{dnprop} not in dinocsv remarks'
                    f'{list(dinoremarks.index.values)}')
                warnings.warn(msg)

        return cls(levels=levels,locprops=locprops, remarks=remarks)


    def name(self):
        """Return water level gauge location name"""
        return self._locprops['locname']


    def levels(self,dropnan=True):
        """Return measured water levels

        Parameters
        ----------
        dropnan : boolean, default True
            drop dates with missing level values

        Returns
        -------
        pd.Series

        """

        if dropnan:
            sr = self._levels['level'].dropna()
        else:
            sr = self._levels['level']

        sr.name = self.name()
        return sr



    def stats(self):
        """Return descriptive statistics of surface water level series"""

        levels = self.levels(dropnan=True)
        sr = Series(dtype='object',name=self._locprops['locname'])

        ##sr['name'] = sr.name
        sr['nmeas'] = levels.count()
        sr['firstyear'] = levels.index.min().year
        sr['lastyear'] = levels.index.max().year

        sr['nyears'] = len(levels.groupby(levels.index.year).count())
        sr['yearspan'] = levels.index.year.max()-levels.index.year.min()+1

        sr['mean'] = levels.mean()
        sr['std'] = levels.std()
        sr['q05'] = levels.quantile(q=0.05)      
        sr['q50'] = levels.quantile(q=0.5)      
        sr['q95'] = levels.quantile(q=0.95)
        sr['q95-q05'] = levels.quantile(q=0.95)- levels.quantile(q=0.05)

        sr['ref'] = self._locprops['level_reference']
        sr['firstdate'] = levels.index.min()
        sr['lastdate'] = levels.index.max()
        sr['alias'] = self._locprops['alias']
        sr['xcr'] = self._locprops['xcr']
        sr['ycr'] = self._locprops['ycr']

        return sr

    def remarks(self,dropnan=True,locname=True):
        """Return remarks

        Parameters
        ----------
        dropnan : bool, default True
            drop rows with empty remarks
        locname : bool, default True
            add column with location name to all rows

        Return
        ------
        pd.Dataframe

        """

        rem = self._remarks.copy()
        rem.insert(0,'date',rem.index)
        rem = rem.reset_index(drop=True)

        if locname:
            rem.insert(0,'location',self.name())

        return rem[rem['remark']!='']

