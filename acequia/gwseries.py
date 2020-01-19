
"""

Base object for maintaining a groundwater series

T.J. de Meij juni 2019

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

class GwSeries:
    """ Init signature: aq.GwSeries(heads=None,ppt=None,srname=None)

        Groundwater series container for groundwater level measurements and piezometer metadata.
        Stores and serves measurements in several units (mwelltop,mref,msurface)
    """

    locprops_names = [
        'locname','filname','alias','xcr','ycr','height_datum',
        'grid_reference'
        ]
    tubeprops_names = [
        'startdate','mplevel','filtop','filbot','surfdate',
        'surflevel'
        ]
    tubeprops_numcols = [
        'mplevel','surflevel','filtop','filbot'
        ]

    mapping_dinolocprops = OrderedDict([
        ('locname','nitgcode'),
        ('filname','filter'),
        ('alias','tnocode'),
        ('xcr','xcoor'),
        ('ycr','ycoor'),
        ('height_datum','NAP'),
        ('grid_reference','RD'),
        ])

    mapping_dinotubeprops = OrderedDict([
        ('startdate','startdatum'),
        ('mplevel','mpcmnap'),
        ('filtop','filtopcmnap'),
        ('filbot','filbotcmnap'),
        ('surfdate','mvdatum'),
        ('surflevel','mvcmnap'),
        ])

    def __repr__(self):
        #return (f'{self.__class__.__name__}(n={len(self._heads)})')
        return (f'{self.name()} (n={len(self._heads)})')


    def __init__(self,heads=None,locprops=None,tubeprops=None):

        if locprops is None:
            self._locprops = Series(index=self.locprops_cols)
        elif isinstance(locprops,pd.Series):
            self._locprops = locprops
        else:
            raise TypeError(f'locprops is not a pandas Series but {type(locprops)}')

        if tubeprops is None:
            self._tubeprops = DataFrame(columns=self.tubeprops_cols)
        elif isinstance(tubeprops,pd.DataFrame):
            ##if tubeprops.empty:
            ##    self._tubeprops = DataFrame(data=[[np.nan]*len(self.tubeprops_cols)],columns=self.tubeprops_cols)
            ##    self._tubeprops.at[0,'startdate'] = heads.index[0]
            ##else:
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
        else:
            raise TypeError(f'heads is not a pandas Series but {type(heads)}')

    @classmethod
    def from_dinogws(cls,filepath):
        """ 
        read tno dinoloket csvfile with groundwater measurements and return data as gwseries object

        parameters
        ----------
        filepath : str


        returns
        -------
        result : GwSeries

        """

        # read dinofile to DinoGws object
        dn = acequia.read.dinogws.DinoGws(filepath=filepath)
        dinoprops = list(dn.header().columns)

        # get location metadata
        locprops = Series(index=cls.locprops_names)

        for propname in cls.locprops_names:
            dinoprop = cls.mapping_dinolocprops[propname]
            if dinoprop in dinoprops:
                locprops[propname] = dn.header().at[0,dinoprop]
                ##locprops['locname'] = dn.header().at[0,'nitgcode']
                ##locprops['filname'] = dn.header().at[0,'filter']
                ##locprops['xcr'] = dn.header().at[0,'xcoor']
                ##locprops['ycr'] = dn.header().at[0,'ycoor']
                ##locprops['alias'] = dn.header().at[0,'tnocode']

        locprops['grid_reference'] = 'RD'
        locprops['height_datum'] = 'mNAP'
        locprops = Series(locprops)

        # get piezometer metadata
        ##tubeprops = dn.header()
        ##coldict = mapping_dinotubeprops
        ##tubeprops = tubeprops.rename(index=str, columns=coldict)
        ##tubeprops = tubeprops[cls.tubeprops_cols]
        tubeprops = DataFrame(columns=cls.tubeprops_names)
        ##dinoprops = list(dn.header().columns)
        for prop in cls.tubeprops_names:
            dinoprop = cls.mapping_dinotubeprops[prop]
            if dinoprop in dinoprops:
                tubeprops[prop] = dn.header()[dinoprop]

        for col in cls.tubeprops_numcols:
                tubeprops[col] = pd.to_numeric(tubeprops[col],
                                 errors='coerce')/100.

        # get head measurements
        sr = dn.series(units="cmmp")/100.

        return cls(heads=sr,locprops=locprops,tubeprops=tubeprops)

    def name(self):
        """ Return groundwater series name """
        return self._locprops['locname']+'_'+self._locprops['filname']

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

        if ref=='mp':
            heads = self._heads
        elif ref in ['datum','surface']:
            heads = self._heads
            for index,props in self._tubeprops.iterrows():
                mask = heads.index>=props['startdate']
                if ref=='datum':
                    heads = heads.mask(mask,props['mplevel']-self._heads)
                elif ref=='surface':
                    surfref = round(props['mplevel']-props['surface'],2)
                    heads = heads.mask(mask,self._heads-surfref)
        else:
            raise ValueError('%s is not a valid reference point name' %ref)
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
