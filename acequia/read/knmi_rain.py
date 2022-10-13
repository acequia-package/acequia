
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


class KnmiRain:
    """Read precipitation data from knmi file"""

    NAMESTR = 'STN,YYYYMMDD,   RD,   SX,' + 'empty'
    ##COLNAMES = ['STN','YYYYMMDD','RD','SX']
    COLNAMES = NAMESTR.replace(' ','').split(',')
    KEEPCOLS = COLNAMES
    VARNAMES = ['prc','snow']
    SNOWCODE = {
        '997': 'gebroken sneeuwdek/broken snow cover < 1 cm',
        '998': 'gebroken sneeuwdek/broken snow cover >=1 cm',
        '999': 'sneeuwhopen/snow dunes}',
        }
    SNOWVALS = {'997':'1','998':'1','999':'1'}
    SKIPROWS = 24


    def __init__(self,filepath=None):

        # NAMESTR[:-1] : trailing colon creates extra column
        self.fpath = Path(filepath)

        if not (self.fpath.exists() and self.fpath.is_file()):
            warnings.warn((f"Filepath '{self.fpath}' not found"
                'empty dataframe is returned.'))
            self.rawdata = pd.DataFrame(columns=self.COLNAMES)
            self.data = pd.DataFrame(columns=self.KEEPCOLS)
        else:
            self.rawdata = self._readfile()
            self.data = self._clean_rawdata(self.rawdata)


    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self.data)})')


    def _readfile(self,fpath):

        # read csv to pd.DataFrame with only str values
        rawdata = pd.read_csv(fpath,sep=',',
            skiprows=self.SKIPROWS,
            names=self.COLNAMES,dtype='str')

        # replace empty strings with NaN
        rawdata = rawdata.apply(
            lambda x: x.str.strip()).replace('', np.nan)

        return rawdata


    def _clean_rawdata(self,rawdata):

        data = rawdata[self.KEEPCOLS].copy()
        for colname in list(data):

            if colname=='YYYYMMDD':
                data[colname] = pd.to_datetime(data[colname],
                    infer_datetime_format=True)
                data = data.set_index(
                    colname,verify_integrity=True)
                data.index.name='date'

            if colname=='RD':
                data[colname] = data[colname].astype(float)/10.

            if colname == 'SX':
                data[colname] = data[colname].replace(self.SNOWVALS)
                data[colname] = data[colname].astype(float)

            if colname == 'empty':
                data = data.drop(columns=[colname])

        return data


    def timeseries(self,var):
        """Return timeseries with data

        Parameters
        ----------
        varname : {'prc')
            variable to return
        """
 
        if var not in self.VARNAMES:
            msg = []
            warnings.warn((f'{var} is not a valid variable name. '
                f'parameter var must be in {self.VARNAMES} '
                f'by default precipitation data are returned.'))
            varname = 'prc'

        if var == 'prc':
            sr = self.data['RD']
            sr.name = 'prc'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]


    @property
    def prc(self):
        """Return precipitation."""
        return self.timeseries('prc')


    @property
    def units(self):
        """Return table with definitions and units of variables"""

        tbl = pd.DataFrame({
            'variable' : ['prc','snow'],
            'datacol' : ['RH','EV24'],
            'unit' : ['mm/day','cm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl

