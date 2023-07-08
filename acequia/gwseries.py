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

from .read import dinogws
from .plots import plotheads as plotheadsmodule
from .stats.gxg import GxgStats
from .stats.gwtimestats import GwTimeStats


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
    _headprops_names = [
        'headdatetime','headmp','headnote','remarks'
        ]

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
        'mplevel','surfacelevel','filbot',
        ]

    _tubeprops_numcols = [
        'mplevel','surfacelevel','filtop','filbot'
        ]

    _reflevels = [
        'datum','surface','mp',
        ]

    _mapping_dinoheadprops = OrderedDict([
        ("headdatetime","peildatum"),("headmp","standcmmp"),
        ("headnote","bijzonderheid"),("remarks","opmerking"),
        ])

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


    def __repr__(self):
        return (f'{self.name()} (n={len(self._heads)})')


    def __init__(self,heads=None,locprops=None,tubeprops=None):
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
            self._locprops = Series(index=self._locprops_names,
                dtype='object')
        elif isinstance(locprops,pd.Series):
            self._locprops = locprops
        else:
            raise TypeError(f'locprops is not a pandas Series but '
                f'{type(locprops)}')

        if tubeprops is None:
            self._tubeprops = DataFrame(columns=self._tubeprops_names)
        elif isinstance(tubeprops,pd.DataFrame):
            self._tubeprops = tubeprops
        else:
            raise TypeError(f'tubeprops is not a pandas DataFrame '
                f'but {type(tubeprops)}')

        if heads is None: 
            self._heads = pd.DataFrame(columns=self._headprops_names) #Series()
            self._heads_original = self._heads.copy()

        elif isinstance(heads,pd.DataFrame):
            self._heads = heads
            self._heads_original = self._heads.copy()

        else:
            raise TypeError(f'heads is not a pandas DataFrame but {type(heads)}')


    def _validate_reference(self,ref):

        if ref is None:
            return self._reflevels[0]

        if ref not in self._reflevels:
            warnings.warn((f'Reference level {ref} is not valid.'
                f'Reference level {self._reflevels[0]} is assumed.'),
                stacklevel=2)
            return self._reflevels[0]

        return ref


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
        ##dn = GwSeries.read.dinogws.DinoGws(filepath=filepath)
        dn = dinogws.DinoGws(filepath=filepath)

        dinoprops = list(dn.header().columns)

        # get location metadata
        locprops = Series(index=cls._locprops_names,dtype='object')

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
        dinoprops = list(dn.headdata().columns)
        heads = DataFrame(columns=cls._headprops_names)
        for prop in cls._headprops_names:
            dinoprop = cls._mapping_dinoheadprops[prop]
            if dinoprop in dinoprops:
                heads[prop] = dn.headdata()[dinoprop]
        heads['headmp'] = heads['headmp']/100.

        return cls(heads=heads,locprops=locprops,tubeprops=tubeprops)

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

        return cls(heads=heads,locprops=locprops,tubeprops=tubeprops)


    def to_json(self,filepath=None):
        """ 
        Create json string from GwWeries object and optionally write 
        to file.

        Parameters
        ----------
        path : str
           Filepath or directory the json file will be written to.
           If filepath is not given no textfile will be written and 
           only OrderedDict with valid JSON wil be retruned.

        Returns
        -------
        OrderedDict with valid json

        Notes
        -----
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

        if os.path.isdir(filepath):
            filepath = os.path.join(filepath,self.name()+'.json')

        try:            
            with open(filepath,"w") as f:
                f.write(json_formatted_str)
        except FileNotFoundError:
            print("Filepath {} does not exist".format(filepath))
            return None
        #finally:
        #    json_dict

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
        filter = str(self._locprops['filname'])
        return location+'_'+filter


    def locname(self):
        """Return series location name"""
        ##srname = self.locprops().index[0]
        ##locname = self.locprops().loc[srname,'locname']
        return self._locprops['locname']


    def locprops(self):
        """Return location properties as pd.DataFrame."""
        locprops = self._locprops
        locprops = locprops.drop('filname')
        locprops = DataFrame(locprops).T.set_index('locname')
        return locprops


    def tubeprops(self,last=False,minimal=False):
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

        if ref not in self._reflevels:
            msg = f'{ref} is not a valid reference level name'
            raise ValueError(msg)

        heads = self._heads[['headdatetime','headmp']]
        heads = heads.set_index('headdatetime',drop=True) ##.squeeze()
        heads.name = self.name()

        headscopy = heads.copy()

        if ref in ['datum','surface']:

            srvals = headscopy.values.flatten()
            srvals2 = headscopy.values.flatten()
            for index,props in self._tubeprops.iterrows():

                mask = heads.index>=props['startdate']
                if ref=='datum':

                    if not pd.api.types.is_number(props['mplevel']):
                        msg = f'{self.name()} tubeprops mplevel is None.'
                        warnings.warn(msg)
                        mp = 0
                    else:
                        mp = props['mplevel']

                    srvals2 = np.where(mask,mp-srvals,srvals2)


                if ref=='surface':
                    if not pd.isnull(props['surfacelevel']):
                        surfref = round(props['mplevel']-props['surfacelevel'],2)
                        srvals2 = np.where(mask,srvals-surfref,srvals2)

                    else:
                        msg = f'{self.name()} surface level is None'
                        warnings.warn(msg)
                        srvals2 = np.where(mask,srvals,srvals)

            heads = Series(srvals2,index=heads.index)
            heads.name = self.name()

        if freq is not None:
            heads = heads.resample(freq).mean()
            heads.index = heads.index.tz_localize(None)

        return heads


    def timestats(self,ref=None):
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


    def describe(self,ref='datum',gxg=False,minimal=True):
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

        srlist.append(self._locprops[self._locprops_minimal])

        tubeprops = (self._tubeprops[self._tubeprops_minimal].tail(1
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

        """
        locprops = self.locprops(minimal=minimal)
        tubeprops = self.tubeprops(last=True,minimal=True)
        tubeprops = tubeprops.set_index('series')

        tbl = pd.merge(locprops,tubeprops,left_index=True,right_index=True,how='outer')

        srstats = self.timestats(ref=ref)
        tbl = pd.merge(tbl,srstats,left_index=True,right_index=True,how='outer')

        if gxg==True:
            gxg = self.gxg()
            tbl = pd.merge(tbl,gxg,left_index=True,right_index=True,how='left')
        """
        return sr


    def tubeprops_changes(self,proptype='mplevel',relative=True):
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
        if relative:
            sr12 = sr12 - sr12[0]

        return sr12


    def plotheads(self,proptype=None,filename=None):
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

        if proptype is None:
            self.headsplot = plotheadsmodule.PlotHeads(ts=[self.heads()])

        if filename is not None:
            self.headsplot.save(filename)

        return self.headsplot


    def gxg(self,ref='datum',minimal=True,name=True):
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


    def xg(self,ref='datum',name=True):
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
        from .stats.quantiles import Quantiles

        qt = Quantiles(self.heads(ref=ref))
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
        from .stats.quantiles import Quantiles
        
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