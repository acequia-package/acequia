

import pathlib
import warnings
import numpy as np
from pandas import Series,DataFrame
import pandas as pd
import acequia as aq

class WaterWeb:
    """Manage WaterWeb network dataset"""

    _coldict = {
        'Lokatie':'sunloc',
        'SUN-kode':'sunsr',
        'NITG-kode':'nitgsr',
        'OLGA-kode':'olga',
        'DERDEN-kode':'derden',
        'X coordinaat':'xcr',
        'Y coordinaat':'ycr',
        'NAP hoogte bovenkant peilbuis':'mpnap',
        'Hoogte maaiveld tov NAP':'mvnap',
        'Hoogte maaiveld tov Nulpunt':'mvmp',
        'Hoogte maaiveld tov maaiveld':'mvmv',
        'NAP hoogte bovenkant filter':'filtopnap',
        'NAP hoogte onderkant filter':'filbotnap',
        'Peilmoment':'peilmoment',
        'Peilstand':'peilcmmp',
        'Peilstand in Meters':'peilmmp',
        'Peilstand tov NAP':'peilcmnap',
        'Peilstand tov NAP in Meters':'peilmnap',
        'Peilstand tov maaiveld':'peilcmmv',
        'Peilstand tov maaiveld in Meters':'peilmmv',
        'Peilkode':'peilcode',
        'Opmerking bij peiling':'peilopm'
        }

    _typedict = {
        'Lokatie':str,
        'SUN-kode':str,
        'NITG-kode':str,
        'OLGA-kode':str,
        'DERDEN-kode':str,
        'X coordinaat':'float64',
        'Y coordinaat':'float64',
        'NAP hoogte bovenkant peilbuis':'float64',
        'Hoogte maaiveld tov NAP':'float64',
        'Hoogte maaiveld tov Nulpunt':'float64',
        'Hoogte maaiveld tov maaiveld':'float64',
        'NAP hoogte bovenkant filter':'float64',
        'NAP hoogte onderkant filter':'float64',
        'Peilstand':str,
        'Peilstand':'float64',
        'Peilstand in Meters':'float64',
        'Peilstand tov NAP':'float64',
        'Peilstand tov NAP in Meters':'float64',
        'Peilstand tov maaiveld':'float64',
        'Peilstand tov maaiveld in Meters':'float64',
        'Peilkode':str,
        'Opmerking bij peiling':str,
        }

    _locprops_cols = ['sunloc','sunsr','nitgsr','olga','derden',
        'xcr','ycr',]

    _tubeprops_cols = ['mpnap','mvnap','filtopnap','filbotnap']

    _peilprops_cols = ['peilmoment','peilcmmp','peilcode','peilopm']

    _locprops_mapping = {
        'locname':'sunloc','alias':'nitgsr',
        'xcr':'xcr','ycr':'ycr'
        }

    _tubeprops_mapping = {
        'startdate':'peilmoment','mplevel':'mpnap',
        'filtop':'filtopnap','filbot':'filbotnap',
        'surfacelevel':'mvnap'
        }

    _levels_mapping = {
        'headdatetime':'peilmoment', 'headmp':'peilcmmp', 
        'headnote':'peilcode','remarks':'peilopm'}


    def __init__(self,fpath=None,data=None,network=None):

        self._fpath = fpath
        self._network = network
        self._data = data

        if ((self._fpath is not None) and (self._data is None)):

            if not pathlib.Path(self._fpath).is_file():
                raise ValueError(f('{self._fpath} is not a valid file path.'))

            self._data = self._readcsv(self._fpath)

        if self._network is None:
            if self._fpath is not None:
                path = pathlib.Path(fpath)
                self._network = path.stem
            else:
                self._network = 'waterweb'

        if self._data is not None:

            if not isinstance(self._data,pd.DataFrame):
                raise ValueError((f'{self._data} is not a valid Pandas ')
                    (f'DataFrame.'))

            self._sunsr = self._data['sunsr'].unique()


    def __repr__(self):
        return (f'{self._network} (n={self.__len__()})') #len(self.srnames())})')

    def __len__(self):
        return len(self.srnames())


    def _readcsv(self,fpath):
        """Read WaterWeb csv file"""

        file = open(fpath,'r')
        self._flines = file.readlines()
        file.close()

        # read flines to list of lists
        datalines = []
        for rownr,line in enumerate(self._flines):

            line = line.rstrip('\n').rstrip(';')

            if rownr==0:
                colnames = [x.strip('"') for x in line.split(';')]
                continue

            elms = [x.strip('"') for x in line.split(';')]
            elms = [x.replace(',','.') for x in elms]

            elms = [x if len(x)>1 else np.nan for x in elms]

            if len(elms)>1:
                datalines.append(elms)

        # create dataframe and do type conversions
        data = pd.DataFrame.from_records(datalines,columns=colnames)
        data = data.astype(dtype=self._typedict)
        data = data.rename(columns=self._coldict)
        data['peilmoment'] = pd.to_datetime(data['peilmoment'])

        return data


    def _readcsv_fast(self,fpath):
        """Read WaterWeb csv file"""

        try:
            data = pd.read_csv(fpath,sep=';',quotechar='"',
                decimal=',', dtype=self._typedict,
                parse_dates=['Peilmoment'])
            data = data.rename(columns=self._coldict)
        except pd.errors.ParserError:
            print("Dit is een error!")
            data = DataFrame()

        return data



    @classmethod
    def read_csv(cls,fpath,network=None):
        """ 
        read waterweb csv network file

        parameters
        ----------
        filepath : str
            path to waterweb csv export file

        network : str, optional
            name of network

        returns
        -------
        WaterWebNetwork object

        """
        data = cls._readcsv(cls,fpath)
        return cls(fpath=fpath,data=data,network=network)


    def srnames(self):
        """Return list of series names"""
        return self._sunsr


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
        filters if more than one filter is present. For well locations 
        with only one filter the location name and filter name would be
        equal. This function always returns an 'A' as filter name for 
        these well locations. """

        filname = self.locprops(srname)['sunsr']
        if filname[-1].isalpha():
            return filname[-1]
        return 'A'


    def network(self,network=None):
        """Return or set network name

        Parameters
        ----------
        network : str, optional
            name of measurement network """

        if isinstance(network,str):
            self._network = network
        return self._network


    def locprops(self,sunsr):
        """Return series location properties

        Parameters
        ----------
        sunsr : str
            name of series to return

        Return
        ------
        pd.Series """

        data = self._data[self._data['sunsr']==sunsr]
        lastrow = data.iloc[-1,:]

        sr = Series(index=self._locprops_cols,dtype='object',
            name=sunsr)
        for col in self._locprops_cols:
            sr[col] = lastrow[col]

        return sr


    def tubeprops(self,sunsr):
        """Return welltube properties

        Parameters
        ----------
        sunsr : str
            name of series

        Returns
        -------
        pd.DataFrame """

        data = self._data[self._data['sunsr']==sunsr]
        data = data.drop_duplicates(subset=self._tubeprops_cols,
            keep='first')
        data = data[['peilmoment']+self._tubeprops_cols]
        data = data.reset_index(drop=True)

        return data


    def levels(self,sunsr,ref='mp'):
        """Return measured levels

        Parameters
        ----------
        sunsr : str
            name of series
        ref : {'mp','datum',' surface'}, default 'mp' 

        Returns
        -------
        pd.Series """

        if ref=='mp':
            col = 'peilcmmp'
        if ref=='nap':
            col = 'peilmnap'
        if ref=='mv':
            col = 'peilcmmv'

        data = self._data[self._data['sunsr']==sunsr]
        data = data[[col,'peilmoment']]
        data = data.set_index('peilmoment',drop=True).squeeze()
        data.name = self.locname(sunsr)
        data.index.name = 'datetime' 
        data = data/100.

        return data


    def gwseries(self,sunsr):
        """Return gwseries obect for one series

        Parameters
        ----------
        sunsr : str
            name of series to return

        Returns
        -------
        acequia.GwSeries

        """

        gw = aq.GwSeries()

        # locprops
        locprops = self.locprops(sunsr)
        for gwprop in list(gw._locprops.index):
            if gwprop not in self._locprops_mapping.keys():
                continue
            wwnprop = self._locprops_mapping[gwprop]
            gw._locprops[gwprop] = locprops[wwnprop]

        gw._locprops['filname'] = self.filname(sunsr)
        gw._locprops['height_datum'] = 'mNAP'
        gw._locprops['grid_reference'] = 'RD'

        # tubeprops
        tubeprops = self.tubeprops(sunsr)
        for gwprop in list(gw._tubeprops):
            if gwprop not in self._tubeprops_mapping.keys():
                continue
            wwnprop = self._tubeprops_mapping[gwprop]
            gw._tubeprops[gwprop] = tubeprops[wwnprop].values
            if gwprop in gw._tubeprops_numcols:
                gw._tubeprops[gwprop] = gw._tubeprops[gwprop]/100.

        #levels
        levels = self._data[self._data['sunsr']==sunsr]
        levels = levels[self._peilprops_cols]
        for gwprop in list(gw._headprops_names):
            if gwprop not in self._levels_mapping.keys():
                continue
            wwnprop = self._levels_mapping[gwprop]
            gw._heads[gwprop] = levels[wwnprop].values
        gw._heads['headmp'] = gw._heads['headmp']/100.

        return gw

