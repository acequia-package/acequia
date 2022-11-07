
import pathlib
import warnings
import numpy as np
from pandas import Series,DataFrame
import pandas as pd
from ..gwseries import GwSeries


class WaterWeb:
    """
    Manage WaterWeb dataset

    Constructor
    -----------
    from_csv
        Read waterweb csv export file and return WaterWeb object.

    Properties
    ----------
    srnames
        Return list of series names.
    type_counts
        Return table of measurement type counts.
    networkname(name=None):
        Network name.

    Methods
    -------
    locname(srname)
        Return location name for given series.
    filname(srname)
        Return filter name for given series.
    measurement_kind(srname)
        Return measurement kind for series srname.
    locprops(srname)
        Return series location properties.
    tubeprops(srname)
        Return welltube properties.
    levels(srname,ref='mp')
        Return measured levels for a series.
    gwseries(srname)
        Return gwseries object for a series.
    """
    _column_mapping = {
        'Lokatie':'sunloc',
        'SUN-kode':'sunsr',
        'NITG-kode':'nitgsr',
         #'OLGA-kode':'olga', #VERVALLEN
        'BROID':'broid',
        'DERDEN-kode':'derden',
        'X coordinaat':'xcr',
        'Y coordinaat':'ycr',
        'NAP hoogte bovenkant peilbuis':'mpnap',
        'Hoogte maaiveld tov NAP':'mvnap',
        'Hoogte maaiveld tov Nulpunt':'mvmp',
        'Hoogte maaiveld tov maaiveld':'mvmv',
        'NAP hoogte bovenkant filter':'filtopnap',
        'NAP hoogte onderkant filter':'filbotnap',
        'Peilmoment':'datetime',
        'Peilstand':'peilcmmp',
        'Peilstand in Meters':'peilmmp',
        'Peilstand tov NAP':'peilcmnap',
        'Peilstand tov NAP in Meters':'peilmnap',
        'Peilstand tov maaiveld':'peilcmmv',
        'Peilstand tov maaiveld in Meters':'peilmmv',
        'Peilkode':'peilcode',
        'Opmerking bij peiling':'peilopm'
        }

    """
    _typedict = {
        'Lokatie':str,
        'SUN-kode':str,
        'NITG-kode':str,
        'BROID':str,
        ##'OLGA-kode':str,
        'DERDEN-kode':str,
        'X coordinaat':'float64',
        'Y coordinaat':'float64',
        'NAP hoogte bovenkant peilbuis':'int64',
        'Hoogte maaiveld tov NAP':'int64',
        'Hoogte maaiveld tov Nulpunt':'int64',
        'Hoogte maaiveld tov maaiveld':'int64',
        'NAP hoogte bovenkant filter':'int64',
        'NAP hoogte onderkant filter':'int64',
        'Peilmoment':str,
        'Peilstand':'int64',
        'Peilstand in Meters':'float64',
        'Peilstand tov NAP':'int64',
        'Peilstand tov NAP in Meters':'float64',
        'Peilstand tov maaiveld':'int64',
        'Peilstand tov maaiveld in Meters':'float64',
        'Peilkode':str,
        'Opmerking bij peiling':str,
        }
    """
    
    _locprops_cols = ['sunloc','sunsr','nitgsr','broid','derden',
        'xcr','ycr',]

    _tubeprops_cols = ['mpnap','mvnap','filtopnap','filbotnap']

    _peilprops_cols = ['datetime','peilcmmp','peilcode','peilopm']

    _locprops_mapping = {
        'locname':'sunloc','alias':'nitgsr',
        'xcr':'xcr','ycr':'ycr'
        }

    _tubeprops_mapping = {
        'startdate':'datetime','mplevel':'mpnap',
        'filtop':'filtopnap','filbot':'filbotnap',
        'surfacelevel':'mvnap'
        }

    _levels_mapping = {
        'headdatetime':'datetime', 'headmp':'peilcmmp', 
        'headnote':'peilcode','remarks':'peilopm'}

    _reflevels = [
        'datum','surface','mp',
        ]

    _measurement_types = ['B','S','L','P']


    def __init__(self,fpath=None,data=None,network=None):

        ##self._fpath = fpath
        self._network = network
        self.data = data

        """
        if ((self._fpath is not None) and (self.data is None)):

            if not pathlib.Path(self._fpath).is_file():
                raise ValueError((f'{self._fpath} is not a valid '
                    'file path.'))

           self.data = self._readcsv(self._fpath)
        """

        #if self._network is None:
        #    if self._fpath is not None:
        #        path = pathlib.Path(fpath)
        #        self._network = path.stem
        #    else:
        if self._network is None:
            self._network = 'Onbekend Waterweb meetnet'

        if self.data is not None:

            if not isinstance(self.data,pd.DataFrame):
                raise ValueError((f'{self.data} is not a valid Pandas '
                    f'DataFrame.'))

    def __repr__(self):
        return (f'{self._network} (n={self.__len__()})')


    def __len__(self):
        return len(self.srnames)


    @classmethod
    def from_csv(cls,fpath,network=None):
        """ 
        Read waterweb csv network file and return new WaterWeb object

        Parameters
        ----------
        filepath : str
            path to waterweb csv export file

        networkname : str, optional
            name of network

        Returns
        -------
        WaterWebNetwork object

        """
        #data = cls._readcsv(cls,fpath)
        data = pd.read_csv(fpath,sep=';',decimal=',')

        #check for missing columns
        missing_columns = []
        for col in WaterWeb._column_mapping.keys():
            if col not in list(data):
                missing_columns.append(col)
        if missing_columns:
            warnings.warn((f'Missing columns in WaterWeb csv file: '
                f'{missing_columns}'))

        # check for unknown columns
        unknown_columns = []
        for col in list(data):
            if col not in WaterWeb._column_mapping.keys():
                unknown_columns.append(col)
        if unknown_columns:
            warnings.warn((f'Unknown columns in WaterWeb csv file: '
                f'{unknown_columns}.'))

        ## change column types
        ##data = data.astype(dtype=cls._typedict)

        # change column contents
        data['Peilmoment'] = pd.to_datetime(data['Peilmoment'])
        data['NITG-kode'] = data['NITG-kode'].apply(
            lambda x:x[:8]+"_"+x[-3:].lstrip('0'))

        # rename columns
        data = data.rename(columns=cls._column_mapping)

        return cls(fpath=fpath,data=data,network=network)


    @property
    def srnames(self):
        """Return list of series names"""
        if self.data is not None:
            return list(self.data['sunsr'].unique())
        else:
            return []

    def measurement_kind(self,srname=None):
        """Return kind of measurement type series

        Parameters
        ----------
        srname : str, optional
            series name, if not given, type of all series is returned

        Returns
        -------
        str, numpy array of str """

        srnames = self.srnames
        sr = Series(data=srnames,index=srnames,name='seriestype')
        sr = sr.apply(lambda x:x[8])

        if srname is not None:
            return sr[srname]

        return sr

    @property
    def type_counts(self):
        """Return table of measurement type counts."""
        srtypelist = []
        for name in self.srnames:
            srtypelist.append(self.measurement_kind(name))
        tbl = pd.Series(srtypelist).value_counts()
        tbl.name = self.networkname
        return tbl


    def locname(self,srname):
        """Return location name for given series

        Parameters
        ----------
        srname : str
            name of series to return """

        return self.locprops(srname)['sunloc']


    def filname(self,srname):
        """Return filter name for given series

        Parameters
        ----------
        srname : str
            name of series to return 

        Notes
        -----
        WaterWeb uses the DINO-SUN convention of only explicitly naming
        filters if more than one filter is present."""

        filname = self.locprops(srname)['sunsr']
        if filname[-1].isalpha():
            return filname[-1]
        return ''


    @property
    def networkname(self):
        """Return network name

        Parameters
        ----------
        name : str, optional
            name of measurement network """
        return self._network

    @networkname.setter
    def networkname(self,name):
        self._network = name

    def locprops(self,srname):
        """Return series location properties

        Parameters
        ----------
        sunsr : str
            name of series to return

        Return
        ------
        pd.Series """

        data =self.data[self.data['sunsr']==srname]
        lastrow = data.iloc[-1,:]

        sr = Series(index=self._locprops_cols,dtype='object',
            name=srname)
        for col in self._locprops_cols:
            sr[col] = lastrow[col]

        return sr


    def tubeprops(self,srname):
        """Return welltube properties

        Parameters
        ----------
        sunsr : str
            name of series

        Returns
        -------
        pd.DataFrame """

        data =self.data[self.data['sunsr']==srname]
        data = data.drop_duplicates(subset=self._tubeprops_cols,
            keep='first')
        data = data[['datetime']+self._tubeprops_cols]
        data = data.reset_index(drop=True)

        return data

    def levels(self,srname,ref='mp'):
        """Return measured levels

        Parameters
        ----------
        srname : str
            name of series
        ref : {'mp','datum',' surface'}, default 'mp' 

        Returns
        -------
        pd.Series """

        if ref not in self._reflevels:
            warnings.warn((f'{ref} not in {self._references}. '),
                (f'reference is set to "datum".')) 
            ref = 'datum'
        if ref=='mp':
            col = 'peilcmmp'
        if ref=='datum':
            col = 'peilmnap'
        if ref=='mv':
            col = 'peilcmmv'

        data =self.data[self.data['sunsr']==srname]
        data = data[[col,'datetime']]
        data = data.set_index('datetime',drop=True).squeeze()
        data.name = self.locname(srname)
        data.index.name = 'datetime' 
        data = data/100.

        return data


    def gwseries(self,srname):
        """Return gwseries obect for one series

        Parameters
        ----------
        srname : str
            name of series to return

        Returns
        -------
        acequia.GwSeries

        """

        gw = GwSeries()

        # locprops
        locprops = self.locprops(srname)
        for gwprop in list(gw._locprops.index):
            if gwprop not in self._locprops_mapping.keys():
                continue
            wwnprop = self._locprops_mapping[gwprop]
            gw._locprops[gwprop] = locprops[wwnprop]

        gw._locprops['filname'] = self.filname(srname)
        gw._locprops['height_datum'] = 'mNAP'
        gw._locprops['grid_reference'] = 'RD'

        # tubeprops
        tubeprops = self.tubeprops(srname)
        for gwprop in list(gw._tubeprops):
            if gwprop not in self._tubeprops_mapping.keys():
                continue
            wwnprop = self._tubeprops_mapping[gwprop]
            gw._tubeprops[gwprop] = tubeprops[wwnprop].values
            if gwprop in gw._tubeprops_numcols:
                gw._tubeprops[gwprop] = gw._tubeprops[gwprop]/100.

        #levels
        levels =self.data[self.data['sunsr']==srname]
        levels = levels[self._peilprops_cols]
        for gwprop in list(gw._headprops_names):
            if gwprop not in self._levels_mapping.keys():
                continue
            wwnprop = self._levels_mapping[gwprop]
            gw._heads[gwprop] = levels[wwnprop].values
        gw._heads['headmp'] = gw._heads['headmp']/100.

        return gw

