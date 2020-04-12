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

import matplotlib as mpl
import matplotlib.pyplot as plt

from pandas import Series, DataFrame
import pandas as pd
import numpy as np

#from .read.dinogws import DinoGws
import acequia.read.dinogws
from .stats.gwgxg import GxG

class GwSeries:
    """ Class that holds and manages a groundwater heads time series

    Parameters
    ----------
    heads : pandas.Series
        timeseries with groundwater heads
    locprops : pandas.Series
        series with location properties
    tubprops : pandas.DataFrame
        dataframe with tube properties in time

    Example
    -------
    gw = GwSeries.from_dinogws(<filepath to dinocsv file>)
    gw = GwSeries.from_json(<filepath to acequia json file>)

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
    _tubeprops_names = [
        'startdate','mplevel','filtop','filbot','surfacedate',
        'surfacelevel'
        ]
    _tubeprops_numcols = [
        'mplevel','surfacelevel','filtop','filbot'
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
        elif isinstance(heads,pd.Series):
            self._heads = heads.copy()
            self._heads.index.name = 'datetime'
            self._heads.name = self.name()
            self._heads_original = self._heads.copy()
        else:
            raise TypeError(f'heads is not a pandas Series but {type(heads)}')


        # load submodules
        self.gxg = GxG(self)


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

    def name(self):
        """ Return groundwater series name """
        location = str(self._locprops['locname'])
        filter = str(self._locprops['filname'])
        return location+'_'+filter

    def heads(self,ref='datum'):
        """ 
        Return groundwater head measurements

        parameters
        ----------
        ref : {'mp','datum','surface'}, default 'datum'

        returns
        -------
        result : pandas time Series

        """

        if ref not in ['mp','datum','surface']:
            raise ValueError('%s is not a valid reference point name' %ref)

        if ref=='mp':
            heads = self._heads
       
        if ref in ['datum','surface']:
            heads = self._heads
            for index,props in self._tubeprops.iterrows():
                mask = heads.index>=props['startdate']
                if ref=='datum':
                    heads = heads.mask(mask,props['mplevel']-self._heads)
                if ref=='surface':
                    surfref = round(props['mplevel']-props['surfacelevel'],2)
                    heads = heads.mask(mask,self._heads-surfref)

        return heads

    def to_csv(self,dirpath=None):
        """Export groundwater series and metadata to csv file

        parameters
        ----------
        dirpath : export directory

        """
        filepath = dirpath+self.name()+'_0.csv'
        self._heads.to_csv(filepath,index=True,index_label='datetime',header=['head'])

        filepath = dirpath+self.name()+'_1.csv'
        self._tubeprops.to_csv(filepath,index=False,header=True)

        filepath = dirpath+self.name()+'_2.csv'
        self._locprops.to_csv(filepath,index=True,header=False)

    @classmethod
    def from_csv(cls,filepath=None):
        """Import groundwater series and metadata from csv file

        parameters
        ----------
        filepath : filename of csv file with groundwater heads

        """
        _heads = pd.read_csv(filepath,header=0,index_col=0,squeeze=True)
        _heads.index = pd.to_datetime(_heads.index)


        filepath = filepath[:-6]+'_1.csv'
        #print(filepath)
        _tubeprops = pd.read_csv(filepath,header=0)

        filepath = filepath[:-6]+'_2.csv'
        #print(filepath)
        _locprops = pd.read_csv(filepath,header=None,index_col=0,squeeze=True)

        return cls(heads=_heads,locprops=_locprops,tubeprops=_tubeprops)

    @classmethod
    def from_json(cls,filepath=None):
        """ Read gwseries object from json file """

        with open(filepath) as json_file:
            json_dict = json.load(json_file)

        locprops = DataFrame.from_dict(json_dict['locprops'],orient='index')
        locprops = Series(data=locprops[0],index=locprops.index,name='locprops')

        tubeprops = DataFrame.from_dict(json_dict['tubeprops'],
                    orient='index')
        tubeprops.name = 'tubeprops'

        heads = DataFrame.from_dict(json_dict['heads'],orient='index')
        srindex = pd.to_datetime(heads.index)
        srname = locprops['locname']+'_'+locprops['filname']
        heads = Series(data=heads[0].values,index=srindex,name=srname)

        return cls(heads=heads,locprops=locprops,tubeprops=tubeprops)

    def to_json(self,dirpath=None):
        """ Write gwseries object to json file 
        
        parameters
        ----------
        dirpath : str
           directory json file will be written to
           (if dirpath is not given no textfile will be written and 
           only OrderedDict with valid JSON wil be retruned)

        returns
        -------
        OrderedDict with valid json

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

        return json_dict

    def series1428(self,nearest=0,ref='datum'):
        """ Return timeseries of measurements on 14th and 28th 

        Parameters
        ----------
        nearest : integer, optional
            maximum number of days a measurement is allowed to deviate
            from the 14th or 28th
        ref : {'mp','datum','surface'}, default 'datum'

        Returns
        -------
        sr : pandas time Series

        """

        if nearest==0:
            is1428 = lambda x: ((x.day == 14) or (x.day ==28))
            sr = self.heads(ref=ref)
            srbool = Series(sr.index.map(is1428), index=sr.index)
            return sr.loc[srbool]

        
        








            