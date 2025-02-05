""" 
This module containes the class GwSeries for managing a head series.

Examples
--------
gw = GwSeries.from_dinogws(<filepath to dinocsv file>)
gw = GwSeries.from_json(<filepath to acequia json file>)
""" 

import math
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

from .._read.dinogws import DinoGws
from .._plots import plotheads as plotheadsmodule
from .._stats.gxg import GxgStats
from .._stats.gwtimestats import GwTimeStats


class GwSeries:
    """ 
    Groundwater heads time series management

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

    Notes
    -----
    Head measurements are stored in meters relative to welltop 
    and served in several units: mwelltop,mref,msurfacelevel.

    Valid row names for locprops and column names for tubeprops are
    stored in class variables locprops_names and tubeprops_names:
    >>> print(acequia.GwSeries.locprops_names)
    >>> print(acequia.GwSeries.tubeprops_names)
       
    """
    HEADPROPS_NAMES = [
        'headdatetime','headmp','headnote','remarks'
        ]

    LOCPROPS_NAMES = [
        'locname','filname','alias','xcr','ycr','height_datum',
        'grid_reference'
        ]

    LOCPROPS_MINIMAL = [
        'locname','filname','alias','xcr','ycr'
        ]

    TUBEPROPS_NAMES = [
        'startdate','mplevel','filtop','filbot','surfacedate',
        'surfacelevel'
        ]

    TUBEPROPS_MINIMAL = [
        'mplevel','surfacelevel','filbot',
        ]

    TUBEPROPS_NUMCOLS = [
        'mplevel','surfacelevel','filtop','filbot'
        ]

    REFLEVELS = [
        'datum','surface','mp',
        ]

    REFLEVEL_DEFAULT = 'datum'

    def __init__(self, heads=None, locprops=None, tubeprops=None):
        """
        Parameters
        ----------
        heads : pandas.DataFrame
            timeseries with groundwater heads
        locprops : pandas.Series
            series with location properties
        tubprops : pandas.DataFrame
            dataframe with tube properties in time

        """

        if locprops is None:
            self._locprops = Series(index=self.LOCPROPS_NAMES,
                dtype='object')
        elif isinstance(locprops,pd.Series):
            self._locprops = locprops
        else:
            raise TypeError(f'locprops is not a pandas Series but '
                f'{type(locprops)}')

        if tubeprops is None:
            self._tubeprops = DataFrame(columns=self.TUBEPROPS_NAMES)
        elif isinstance(tubeprops,pd.DataFrame):
            self._tubeprops = tubeprops
        else:
            raise TypeError(f'tubeprops is not a pandas DataFrame '
                f'but {type(tubeprops)}')

        if heads is None: 
            self._obs = pd.DataFrame(columns=self.HEADPROPS_NAMES) #Series()
            self._obs_original = self._obs.copy()

        elif isinstance(heads,pd.DataFrame):
            self._obs = heads
            self._obs_original = self._obs.copy()

        else:
            raise TypeError(f'heads is not a pandas DataFrame but {type(heads)}')

    def __repr__(self):
        return (f'{self.name()} (n={len(self)})')

    def __len__(self):
        return len(self._obs)

    def _validate_reference(self,ref):

        if ref is None:
            return self.REFLEVELS[0]

        if ref not in self.REFLEVELS:
            warnings.warn((f'Reference level {ref} is not valid.'
                f'Reference level {self.REFLEVELS[0]} is assumed.'),
                stacklevel=2)
            return self.REFLEVELS[0]

        return ref

    @classmethod
    def from_dinogws(cls,filepath):
        """Read measured groundwater heads from dinoloket csv file."""

        # create DinoGws object with groundwater level data
        dn = DinoGws(filepath=filepath,readall=True)

        # get location metadata
        locprops = Series(index=cls.LOCPROPS_NAMES,dtype='object')

        for propname in cls.LOCPROPS_NAMES:
            dinoprop = DinoGws.MAPPING_DINOLOCPROPS[propname]
            if dinoprop in DinoGws.FILTERCOLS:
                locprops[propname] = dn.header.at[0,dinoprop]

        locprops['grid_reference'] = 'RD'
        locprops['height_datum'] = 'mNAP'
        locprops = Series(locprops)

        # get piezometer metadata
        tubeprops = DataFrame(columns=cls.TUBEPROPS_NAMES)
        for prop in cls.TUBEPROPS_NAMES:
            dinoprop = DinoGws.MAPPING_DINOTUBEPROPS[prop]
            if dinoprop in DinoGws.FILTERCOLS:
                tubeprops[prop] = dn.header[dinoprop]

        for col in cls.TUBEPROPS_NUMCOLS:
                tubeprops[col] = pd.to_numeric(tubeprops[col],
                                 errors='coerce')/100.

        # get head measurements
        heads = DataFrame(columns=cls.HEADPROPS_NAMES)
        for prop in cls.HEADPROPS_NAMES:
            dinoprop = DinoGws.MAPPING_DINOHEADPROPS[prop]
            if dinoprop in DinoGws.HEADCOLS:
                heads[prop] = dn.headdata[dinoprop]
        heads['headmp'] = heads['headmp']/100.

        return cls(heads=heads, locprops=locprops, tubeprops=tubeprops)


    @classmethod
    def from_json(cls,filepath=None):
        """ Read gwseries object from json file """

        with open(filepath) as json_file:
            json_dict = json.load(json_file)

        # locprops
        locprops = DataFrame.from_dict(
            json_dict['locprops'],orient='index')
        locprops = Series(data=locprops[0], index=locprops.index,
            name='locprops')

        # tubeprops
        tubeprops = DataFrame.from_dict(
            json_dict['tubeprops'], orient='index')
        tubeprops.name = 'tubeprops'
        tubeprops['startdate'] = pd.to_datetime(tubeprops['startdate']) #.dt.date

        # heads
        heads = DataFrame.from_dict(json_dict['heads'],orient='index')
        heads['headdatetime'] = pd.to_datetime(heads['headdatetime']) #, errors='coerce')

        return cls(heads=heads, locprops=locprops, tubeprops=tubeprops)


    def to_json(self, path=None):
        """ 
        Create json string from GwWeries object and optionally write 
        to file.

        Parameters
        ----------
        path : str, optional
           Valid path name. Can be valid filepath or existing directory. the json file will be written to.
           If filepath is not given no textfile will be written and 
           only OrderedDict with valid JSON wil be retruned.

        Returns
        -------
        OrderedDict with valid json

        Notes
        -----
        If no value for path is given, only a json string is
        returned. 
        If path is the nasme of an existing directory, a json file 
        will be written to a file with the series name.
            
        """

        # create json string with series data
        json_locprops = json.loads(
            self._locprops.to_json()
            )
        json_tubeprops = json.loads(
            self._tubeprops.to_json(date_format='iso',orient='index')
            )
        json_heads = json.loads(
            self._obs.to_json(date_format='iso',orient='index',
            date_unit='s')
            )
            
        json_dict = OrderedDict()
        json_dict['locprops'] = json_locprops
        json_dict['tubeprops'] = json_tubeprops
        json_dict['heads'] = json_heads
        json_formatted_str = json.dumps(json_dict, indent=2)

        # create filepath name
        if os.path.isdir(path):
            filepath = os.path.join(path, f'{self.name()}.json')
        else:
            # todo: test if path is valid filepath
            filepath = path
            if not filepath.endswith('.json'):
                filepath = f'{filepath}.json'

        # write json to file
        try:            
            with open(filepath,"w") as f:
                f.write(json_formatted_str)
        except FileNotFoundError:
            raise ValueError((f'Not a valid filepath: {filepath}'))

        return json_dict


    def to_csv(self,path=None,ref=None):
        """
        Export groundwater heads series to simple csv file.

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
        tube = self.tube()
        return location+'_'+tube

    def tube(self):
        return str(self._locprops['filname'])

    def obs(self):
        return self._obs

    def locname(self):
        """Return series location name"""
        return self._locprops['locname']


    def locprops(self):
        """Return location properties as pd.DataFrame."""
        locprops = self._locprops
        locprops = locprops.drop('filname')
        locprops = DataFrame(locprops).T.set_index('locname')
        return locprops


    def tubeprops(self, last=False, minimal=False):
        """
        Return tube properties.

        Parameters
        ----------
        last : booean, default False
            retun only the last row of tube properties without date

        minimal : bool, default False
            return only minimal selection of columns

        Returns
        -------
        pd.DataFrame
        """
        tps = DataFrame(self._tubeprops[self.TUBEPROPS_NAMES]).copy()
        tps['startdate'].apply(pd.to_datetime, errors='coerce')

        if minimal:
            tps = tps[self.TUBEPROPS_MINIMAL]

        tps.insert(0,'series',self.name())

        if last:
            tps = tps.tail(1)

        return tps

    def surface(self):
        """Return last known surface level"""
        surf = self._tubeprops['surfacelevel'].iat[-1]
        if surf is None:
            surf = np.nan
        return surf

    def obs(self):
        """Return head observations withj notes and remarks."""
        return self._obs

    def heads(self, ref='datum', freq=None):
        """ 
        Return groundwater head measurements.

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
        applied.
        Valid values for 'freq' would be:
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

        if ref not in self.REFLEVELS:
            msg = f'{ref} is not a valid reference level name'
            raise ValueError(msg)

        if self._obs.empty:
            return Series(name=self.name())

        # create heads timeseries from observations
        heads = self._obs[['headdatetime','headmp']]
        heads = heads.set_index('headdatetime',drop=True).squeeze(axis='columns')
        heads = heads.fillna(value=np.nan)
        heads.name = self.name()

        if ref in ['datum','surface']:
        
            headscopy = heads.copy()
            srvals = headscopy.values.flatten()
            #srvals2 = headscopy.values.flatten()
            
            for index,props in self._tubeprops.iterrows():

                mask = heads.index>=props['startdate']
                if ref=='datum':

                    if not pd.api.types.is_number(props['mplevel']):
                        msg = f'{self.name()} tubeprops mplevel is None.'
                        warnings.warn(msg)
                        mp = np.nan
                    else:
                        mp = props['mplevel']

                    srvals2 = np.where(mask, mp-srvals, srvals)

                elif ref=='surface':
                    if not pd.isnull(props['surfacelevel']):
                        surfref = round(props['mplevel']-props['surfacelevel'],2)
                        srvals2 = np.where(mask, srvals-surfref, srvals)

                    else:
                        warnings.warn((f'{self.name()} surface level is None'))
                        srvals2 = np.where(mask, srvals, srvals)

            heads = Series(srvals2,index=heads.index)
            heads.name = self.name()

        if freq is not None:
            heads = heads.resample(freq).mean()
            heads.index = heads.index.tz_localize(None)

        return heads.dropna()

    def get_headnotes(self, kind='all'):
        """Return missing head observation notes.
        
        Parameters
        ----------
        kind : str | list
            Kind of missing head notes to return.

        Notes
        -----
        Possible values of missing head notes are:
        'B' : Ground water frozen ("Bevroren")
        'D' : Well tube was Dry ("Droog")
        'E' : Well tube is defect.
        'M' : Influence of artifical pumping ("beMaling")
        'N' : No observation made ("Niet opgenomen").
        'O' : Overflow of well ("Overloop")
        'V' : Blockage in well ("Verstopping")
        'W' : Well is below Water surface ("Water")
           
        """
        WELLNOTE_TYPES = ['all','B','D','E','M','N','O','V','W']
        if isinstance(kind, str):
            kind = [kind]
        if not all([x in WELLNOTE_TYPES for x in kind]):
            raise ValueError((f'{kind} contains invalid wellnote type.'))

        df = self.obs()[['headdatetime','headnote']]
        sr = df.set_index('headdatetime').squeeze(axis='columns').dropna()

        if 'all' not in kind:
            sr = sr[sr.isin(kind)]
        return sr

    def timestats(self, ref=None):
        """
        Return descriptive statistics for heads time series.

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
            reference level for groundwater heads

        Returns
        -------
        pd.Series
        """

        self._ref = self._validate_reference(ref)

        ts = self.heads(ref=ref)
        gwstats = GwTimeStats(ts)

        return gwstats.stats()


    def describe(self, ref='datum', gxg=False, minimal=True):
        """
        Return selection of properties and descriptive statistics.

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
            choosen reference level for groundwater heads
        gxg : bool, default False
            add GxG descriptive statistics
        minimal : bool, default True
            return minimal selection of statistics

        Returns
        -------
        pd.Series
        """

        self._ref = self._validate_reference(ref)

        srlist = []

        srlist.append(self._locprops[self.LOCPROPS_MINIMAL])

        tubeprops = (self._tubeprops[self.TUBEPROPS_MINIMAL].tail(1
            ).iloc[0,:])
        srlist.append(tubeprops)

        timestats = self.timestats(ref=self._ref)
        srlist.append(timestats)

        if gxg==True:
            gxg = self.gxg(ref=self._ref,minimal=minimal)
            srlist.append(gxg)

        sr = pd.concat(srlist,axis=0)
        sr.name = self.name()

        if self._ref=='surface':

            for key in ['filbot']:
                sr[key] = (sr['surfacelevel']-sr[key])*100

            for key in ['mean','median','q05','q95','dq0595']:
                sr[key] = sr[key]*100

            for key in ['filbot','mean','median','q05','q95',
                'dq0595','n1428']:
                if not np.isnan(sr[key]):
                    sr[key] = math.floor(sr[key])

        return sr


    def tubeprops_changes(self, proptype='mplevel', relative=True):
        """
        Return timeseries with tubeprops changes.

        Parameters
        ----------
        proptype : ['mplevel','surfacelevel','filtop','filbot'
            Tubeproperty that is shown in reference cange graph.
        relative : bool, default True
            Changes relative to first value.

        Returns
        -------
        pd.Series
        """
        if proptype not in ['mplevel','surfacelevel','filtop','filbot']:
            warnings.warn((f'{proptype} is not a valid tube reference '
                f'level. "mplevel"will be used instead.'))
            proptype = 'mplevel'

        sr = self._tubeprops[['startdate','mplevel']].set_index('startdate').squeeze(axis='columns')

        # create list of dates
        from_dates = sr.index.values[:]
        to_dates = sr.index.values[1:] - np.timedelta64(1,'D')
        lastdate = self._obs['headdatetime'].values[-1]
        to_dates = np.append(to_dates, lastdate)
        dates = [item for sublist in zip(from_dates, to_dates) for item in sublist]

        values = np.repeat(sr.values, 2)
        changes = Series(values, index=dates)

        if relative:
            changes = changes - changes[0]

        return changes


    def plotheads(self, proptype=None, filename=None):
        """
        Plot groundwater heads time series.

        Parameters
        ----------
        proptype : ['mplevel','surfacelevel','filtop','filbot'
            Tubeproperty that is shown in reference cange graph.
            If not given, no reference plot will be shown.
        """
        if proptype in ['mplevel','surfacelevel','filtop','filbot']:
            ##mps = self._tubeprops[proptype].values
            mps = self.tubeprops_changes(proptype=proptype)
            self.headsplot = plotheadsmodule.PlotHeads(ts=[self.heads()],mps=mps)
        elif proptype is None:
            self.headsplot = plotheadsmodule.PlotHeads(ts=[self.heads()])
        else:
            raise ValueError((f'Invalid value for proptype: {proptype}',))

        if filename is not None:
            self.headsplot.save(filename)

        return self.headsplot


    def gxg(self, ref='datum', minimal=True, name=True):
        """
        Return tables with desciptive statistics GxG and xG.

        Parameters
        ----------
        ref : {'datum','surface'}, default 'datum'
            Reference level for gxg statistics.
        minimal : bool, default False
            Return minimal set of statistics.
        name : bool, default True
            Include series name in multiindex of xg.

        Returns
        -------
        gxg : pd.Series
            gxg descriptive statistics
        """
        # Calculating gxg can take considerable time. Therefore,
        # results are stored.
        if not hasattr(self,'_gxg'):
            self._gxg = GxgStats(self)            

        gxg = self._gxg.gxg(reference=ref,minimal=minimal)
        
        return gxg


    def xg(self, ref='datum', name=True):
        """
        Return tables with xg desciptive statistics for each year.

        Parameters
        ----------
        ref : {'datum','surface'}, default 'datum'
            Reference level for gxg statistics.
        name : bool, default True
            Include series name in multiindex of xg.

        Returns
        -------
        xg : pd.DataFrame
        """
        if not hasattr(self,'_gxg'):
            self._gxg = GxgStats(self)            

        xg = self._gxg.xg(reference=ref,name=name)

        return xg

    def get_quantiles(self, ref='surface', unit='days', step=None):
        """Calculate quantiles of measured heads.

        Parameters
        ----------
        headsref : {'datum','surface'}, default 'surface'
            Reference level for measurements.
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        pandas.DataFrame
        """
        # bypass circular import
        from .._stats.quantiles import Quantiles

        qt = Quantiles(self.heads(ref=ref, unit=unit, step=step))
        return qt.get_quantiles()

    def get_ecostats(self, ref='surface', units='days', step=5):
        """Return ecological most relevant statistics.

        Parameters
        ----------
        ref : {'datum','surface'}, default 'surface'
            Reference level for measurements.
        units : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int, default 5
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        pandas.Series      
        """

        # bypass circular import
        from .._stats.quantiles import Quantiles
        
        qt = Quantiles(self.heads(ref=ref))
        inundation = qt.get_inundation()
        lowest = qt.get_lowest()

        ecostats = self.gxg(ref='surface',minimal=True)
       
        ecostats['lowest_mean'] = lowest['mean']
        ecostats['lowest_min'] = lowest['min']
        ecostats['lowest_max'] = lowest['max']

        ecostats['inundation_mean'] = inundation['mean']
        ecostats['inundation_min'] = inundation['min']            
        ecostats['inundation_max'] = inundation['max']

        return ecostats