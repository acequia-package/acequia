""" This module contains the base object GwSeries for maintaining a 
groundwater series

Examples
--------
gw = GwSeries.from_dinogws(<filepath to dinocsv file>)
gw = GwSeries.from_json(<filepath to acequia json file>)


""" 

import os
import os.path
from collections import OrderedDict
import json
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt

from pandas import Series, DataFrame
import pandas as pd
import numpy as np

#from .read.dinogws import DinoGws
import acequia.read.dinogws
from .plots.plotheads import PlotHeads
from .stats.gxg import Gxg
from .stats.timestats import TimeStats

class GwSeries:
    """ Groundwater heads time series management

    Methods
    -------
    from_dinogws(filepath)
        read heads series from dinoloket csv file

    from_json(filepath)
        read heads series from json file

    to_json(filepath)
        read heads series from json file

    to_csv(filepath)
        read heads series from json file


    heads(ref,freq)
        return timeseries with measured heads

    name()
        return heads series name

    locprops(minimal)
        return location properties, optional minimal=True

    tubeprops(last)
        return tube properties, optinal only last row (last=True)

    stats(ref)
        return descriptice statistics

    describe()
        return selection of properties and descriptive statistics

    gxg()
        return tabel with gxg (desciptive statistics for groundwater 
        series used in the Netherlands)


    Examples
    --------
    To create a GwSeries object from file:
    >>>gw = GwSeries.from_dinogws(<filepath to dinocsv file>)
    >>>gw = GwSeries.from_json(<filepath to acequia json file>)

    To get GwSeries properties:
    >>>GwSeries.heads()
    >>>GwSeries.locprops()
    >>>GwSeries.name()
    >>>GwSeries.heads1428()

    To export GwSeries data:
    >>>GwSeries.to_csv(<filename>)
    >>>GwSeries.To_json(<filename>)

    Note
    ----
    Head measurements are stored in meters relatieve to welltopStores
    and served in several units: mwelltop,mref,msurfacelevel.

    Valid row names for locprops and column names for tubeprops are
    stored in class variables locprops_names and tubeprops_names:
    >>> print(acequia.GwSeries.locprops_names)
    >>> print(acequia.GwSeries.tubeprops_names)

    """

    _locprops_names = [
        'locname','filname','alias','xcr','ycr','height_datum',
        'grid_reference'
        ]
    _locprops_minimal = [
        'locname','filname','alias','xcr','ycr'
        ]
    _tubeprops_names = [
        'startdate','mplevel','filtop','filbot','surfacedate',
        'surfacelevel'
        ]
    _tubeprops_minimal = [
        'mplevel','filbot','surfacelevel'
        ]
    _tubeprops_numcols = [
        'mplevel','surfacelevel','filtop','filbot'
        ]
    _reflevels = [
        'mp','datum','surface'
        ]

    _mapping_dinolocprops = OrderedDict([
        ('locname','nitgcode'),
        ('filname','filter'),
        ('alias','tnocode'),
        ('xcr','xcoor'),
        ('ycr','ycoor'),
        ('height_datum','NAP'),
        ('grid_reference','RD'),
        ])

    _mapping_dinotubeprops = OrderedDict([
        ('startdate','startdatum'),
        ('mplevel','mpcmnap'),
        ('filtop','filtopcmnap'),
        ('filbot','filbotcmnap'),
        ('surfacedate','mvdatum'),
        ('surfacelevel','mvcmnap'),
        ])


    """
    TODO:
    Additional functionality in this class is provided by subclasses:
    .plot : plotting series
    .gxg  : calculating gxg (statistics used in the Netherlands)
    """


    def __repr__(self):
        return (f'{self.name()} (n={len(self._heads)})')


    def __init__(self,heads=None,locprops=None,tubeprops=None):
        """
        Parameters
        ----------
        heads : pandas.Series
            timeseries with groundwater heads
        locprops : pandas.Series
            series with location properties
        tubprops : pandas.DataFrame
            dataframe with tube properties in time
        """

        if locprops is None:
            self._locprops = Series(index=self._locprops_names)
        elif isinstance(locprops,pd.Series):
            self._locprops = locprops
        else:
            raise TypeError(f'locprops is not a pandas Series but {type(locprops)}')


        if tubeprops is None:
            self._tubeprops = DataFrame(columns=self._tubeprops_names)
        elif isinstance(tubeprops,pd.DataFrame):
            self._tubeprops = tubeprops
        else:
            #self._tubeprops = tubeprops
            raise TypeError(f'tubeprops is not a pandas DataFrame but {type(tubeprops)}')


        if heads is None: 
            self._heads = pd.Series()
            self._heads.index.name = 'datetime'
            self._heads.name = 'unknown'
            self._heads_original = self._heads.copy()

        elif isinstance(heads,pd.Series):
            self._heads = heads.copy()
            self._heads.index.name = 'datetime'
            self._heads.name = self.name()
            self._heads_original = self._heads.copy()

        else:
            raise TypeError(f'heads is not a pandas Series but {type(heads)}')

        # load subclasses
        ##self.gxg = GxG(self.heads)
        ##_timestats = TimeStats(self,name=self._heads.name)


    @classmethod
    def from_dinogws(cls,filepath):
        """ 
        Read tno dinoloket csvfile with groundwater measurements and return data as gwseries object

        Parameters
        ----------
        filepath : str
            path to dinocsv file with measured groundwater heads

        Returns
        -------
        result : GwSeries object

        Example
        -------
        gw = GwSeries.from_dinogws(<filepath>)
        jsondict = gw.to_json(<filepath>)
        gw.from_json(<filepath>)
        
        """

        # read dinofile to DinoGws object
        dn = acequia.read.dinogws.DinoGws(filepath=filepath)
        dinoprops = list(dn.header().columns)

        # get location metadata
        locprops = Series(index=cls._locprops_names)

        for propname in cls._locprops_names:
            dinoprop = cls._mapping_dinolocprops[propname]
            if dinoprop in dinoprops:
                locprops[propname] = dn.header().at[0,dinoprop]

        locprops['grid_reference'] = 'RD'
        locprops['height_datum'] = 'mNAP'
        locprops = Series(locprops)

        # get piezometer metadata
        tubeprops = DataFrame(columns=cls._tubeprops_names)
        for prop in cls._tubeprops_names:
            dinoprop = cls._mapping_dinotubeprops[prop]
            if dinoprop in dinoprops:
                tubeprops[prop] = dn.header()[dinoprop]

        for col in cls._tubeprops_numcols:
                tubeprops[col] = pd.to_numeric(tubeprops[col],
                                 errors='coerce')/100.

        # get head measurements
        sr = dn.series(units="cmmp")/100.

        return cls(heads=sr,locprops=locprops,tubeprops=tubeprops)


    @classmethod
    def from_json(cls,filepath=None):
        """ Read gwseries object from json file """

        with open(filepath) as json_file:
            json_dict = json.load(json_file)

        locprops = DataFrame.from_dict(json_dict['locprops'],
                                        orient='index')
        locprops = Series(data=locprops[0],index=locprops.index,
                                        name='locprops')

        tubeprops = DataFrame.from_dict(json_dict['tubeprops'],
                    orient='index')
        tubeprops.name = 'tubeprops'
        tubeprops['startdate'] = pd.to_datetime(tubeprops['startdate']) #.dt.date

        heads = DataFrame.from_dict(json_dict['heads'],orient='index')
        srindex = pd.to_datetime(heads.index)
        srname = locprops['locname']+'_'+locprops['filname']
        heads = Series(data=heads[0].values,index=srindex,name=srname)

        return cls(heads=heads,locprops=locprops,tubeprops=tubeprops)


    def to_json(self,dirpath=None):
        """ Create json string from GwWeries object and optionally
            write to file 
        
        Parameters
        ----------
        dirpath : str
           directory json file will be written to
           (if dirpath is not given no textfile will be written and 
           only OrderedDict with valid JSON wil be retruned)

        Returns
        -------
        OrderedDict with valid json

        Note
        ----
        If no value for dirpath is given, a valid json string is
        returned. If a value for dirpath is given, nothing is returned 
        and a json file will be written to a file with the series name
        in dirpath.

        """

        json_locprops = json.loads(
            self._locprops.to_json()
            )
        json_tubeprops = json.loads(
            self._tubeprops.to_json(date_format='iso',orient='index')
            )
        json_heads = json.loads(
            self._heads.to_json(date_format='iso',orient='index',
            date_unit='s')
            )

        json_dict = OrderedDict()
        json_dict['locprops'] = json_locprops
        json_dict['tubeprops'] = json_tubeprops
        json_dict['heads'] = json_heads
        json_formatted_str = json.dumps(json_dict, indent=2)

        if isinstance(dirpath,str):
            try:
                filepath = os.path.join(dirpath,self.name()+'.json')
                with open(filepath,"w") as f:
                    f.write(json_formatted_str)
            except FileNotFoundError:
                print("Filepath {} does not exist".format(filepath))
                return None
            finally:
                json_dict

        return json_dict


    def to_csv(self,path=None,ref=None):
        """Export groundwater heads series to simple csv file

        Parameters
        ----------
        path : str
            csv file wil be exported to path, if path is a directory,
            series will be saved as <path><name>.csv.
            if path is not given, file is saved in present directory.

        Examples
        --------
        Save heads to simple csv:
        >>>aq.GwSeries.to_csv(<dirpath>)
        Read back with standard Pandas:
        >>>pd.read_csv(<filepath>,  parse_dates=['date'], 
                  index_col='date', squeeze=True) 
        
        """
        self._csvpath = path
        self._csvref = ref

        if self._csvpath is None:
            self._csvpath = f'{self.name()}.csv'

        if os.path.isdir(self._csvpath):
            filename = f'{self.name()}.csv'
            self._csvpath = os.path.join(self._csvpath,filename)

        try:
            sr = self.heads(ref=self._csvref)
            sr.to_csv(self._csvpath,index=True,index_label='datetime',
                header=['head'])
        except FileNotFoundError:
            msg = f'Filepath {self._csvpath} not found'
            warnings.warn(msg)
            result = None
        else:
            result = sr

        return result


    def name(self):
        """ Return groundwater series name """
        location = str(self._locprops['locname'])
        filter = str(self._locprops['filname'])
        return location+'_'+filter


    def locname(self):
        """Return series location name"""
        srname = self.locprops().index[0]
        locname = self.locprops().loc[srname,'locname']
        return locname


    def locprops(self,minimal=False):
        """ return location properties as pd.DataFrame

        Parameters
        ---------=
        minimal : bool, default=False
            return only minimal selection of columns

        Returns
        -------
        pd.DataFrame"""

        sr = self._locprops
        sr.name = self.name()
        locprops = DataFrame(sr).T
        if minimal:
            locprops = locprops[self._locprops_minimal]
        return locprops


    def tubeprops(self,last=False,minimal=False):
        """Return tube properties 

        Parameters
        ----------
        last : booean, default False
            retun only the last row of tube properties without date

        minimal : bool, default False
            return only minimal selection of columns

        Returns
        -------
        pd.DataFrame"""


        tps = DataFrame(self._tubeprops[self._tubeprops_names]).copy()
        #tps['startdate'] = tps['startdate'].dt.date
        tps['startdate'].apply(pd.to_datetime, errors='coerce')

        if minimal:
            tps = tps[self._tubeprops_minimal]

        tps.insert(0,'series',self.name())

        if last:
            #tps = tps.iloc[[-1]]
            tps = tps.tail(1)
            #tps = tps.set_index('series')

        return tps

    def surface(self):
        """Return last known surface level"""
        return self._tubeprops['surfacelevel'].iat[-1]


    def heads(self,ref='datum',freq=None):
        """ 
        Return groundwater head measurements

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
               choosen reference for groundwater heads
        freq : None or any valid Pandas Offset Alias
                determine frequency of time series

        Returns
        -------
        result : pandas time Series

        Notes
        ----=
        Parameter 'ref' determines the reference level for the heads:
        'mp'   : elative to well top ('measurement point')
        'datum': relative to chosen level (would be meter +NAP for the
                 Netherlands, or TAW for Belgium)
        'surface' : relative to surface level (meter min maaiveld)

        Parameter 'freq' determines the time series frequency by setting
        the Pandas Offset Alias. When 'freq' is None, no resampling is
        applied. Logical values for 'freq' would be:
        'H' : hourly frequency
        'D' : calender day frequency
        'W' : weekly frequency
        'M' : month end frequency
        'MS': month start freuency
        'Q' : quarter end frequency
        'QS': quarter start frequency
        'A' : year end frequency
        'AS': year start frequency
        
        """

        if not ref:
            ref = 'datum'

        if ref not in self._reflevels:
            msg = f'{ref} is not a valid reference point name'
            raise ValueError(msg)

        if ref=='mp':
            heads = self._heads
       
        if ref in ['datum','surface']:
            heads = self._heads
            for index,props in self._tubeprops.iterrows():
                mask = heads.index>=props['startdate']
                if ref=='datum':
                    #if props['mplevel'] is None:
                    if not pd.api.types.is_number(props['mplevel']):
                        msg = f'{self.name()} tubeprops mplevel is None.'
                        warnings.warn(msg)
                        mp = 0
                    else:
                        mp = props['mplevel']
                    heads = heads.mask(mask,mp-self._heads)
                if ref=='surface':
                    if not pd.isnull(props['surfacelevel']):
                        surfref = round(props['mplevel']-props['surfacelevel'],2)
                        heads = heads.mask(mask,self._heads-surfref)
                    else:
                        msg = f'{self.name()} surface level is None'
                        warnings.warn(msg)
                        heads = heads.mask(mask,self._heads)

        if freq is not None:
            heads = heads.resample(freq).mean()
            heads.index = heads.index.tz_localize(None)

        return heads


    def timestats(self,ref=None):
        """Return descriptice statistics

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
            choosen reference level for groundwater heads

        Returns
        -------
        pd.DataFrame """

        #sr = gw.heads(ref='surface')
        #self._timestats.stats(ref=ref)

        if not ref:
            ref = 'datum'

        ts = self.heads(ref=ref)
        stats = TimeStats(ts)

        #tp = self.tubeprops(last=True,minimal=True)

        return stats.stats()


    def describe(self,ref=None,gxg=False):
        """Return selection of properties and descriptive statistics

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
            choosen reference level for groundwater heads
        gxg : bool, default False
            add GxG descriptive statistics

        Returns
        -------
        pd.DataFrame """

        if not ref:
            ref = 'datum'

        locprops = self.locprops(minimal=True)
        tubeprops = self.tubeprops(last=True,minimal=True)
        tubeprops = tubeprops.set_index('series')

        tbl = pd.merge(locprops,tubeprops,left_index=True,right_index=True,how='outer')

        srstats = self.timestats(ref=ref)
        tbl = pd.merge(tbl,srstats,left_index=True,right_index=True,how='outer')

        if gxg==True:
            gxg = self.gxg()
            tbl = pd.merge(tbl,gxg,left_index=True,right_index=True,how='left')

        return tbl


    def tubeprops_changes(self,proptype='mplevel'):
        """Return timeseries with tubeprops changes

        Parameters
        ----------
        proptype : ['mplevel','surfacelevel','filtop','filbot'
            tubeproperty that is shown in reference cange graph

        Returns
        -------
        pd.Series

        """

        if proptype in ['mplevel','surfacelevel','filtop','filbot']:
            mps = self._tubeprops[proptype].values
        else:
            mps = self._tubeprops['mplevel']
            # TODO: add userwarning

        idx = pd.to_datetime(self._tubeprops['startdate'])
        sr1 = Series(mps,index=idx)

        idx = sr1.index[1:]-pd.Timedelta(days=1)
        lastdate = self.heads().index[-1]
        idx = idx.append(pd.to_datetime([lastdate]))
        sr2 = Series(mps,index=idx)

        sr12 = pd.concat([sr1,sr2]).sort_index()
        sr12 = sr12 - sr12[0]

        return sr12


    def plotheads(self,proptype=None,filename=None):
        """Plot groundwater heads time series

        Parameters
        ----------
        proptype : ['mplevel','surfacelevel','filtop','filbot'
            tubeproperty that is shown in reference cange graph
            if not given, no reference plot will be shown

        """
        if proptype in ['mplevel','surfacelevel','filtop','filbot']:
            ##mps = self._tubeprops[proptype].values
            mps = self.tubeprops_changes(proptype=proptype)
            self.headsplot = PlotHeads(ts=[self.heads()],mps=mps)

        if proptype is None:
            self.headsplot = PlotHeads(ts=[self.heads()])

        if filename is not None:
            self.headsplot.save(filename)


    def gxg(self,ref=None):
        """Return table with Gxg desciptive statistics"""
        self._Gxg = Gxg(self, ref=ref)
        return self._Gxg.gxg()

