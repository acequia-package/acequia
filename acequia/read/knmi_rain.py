
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


class KnmiRain:
    """Read precipitation data from knmi file"""

    NAMESTR = 'STN,YYYYMMDD,   RD,   SX,' + 'empty'
    ##COLNAMES = ['STN','YYYYMMDD','RD','SX']
    VARNAMES = ['prc','snow']
    SNOWCODE = {
        '997': 'gebroken sneeuwdek/broken snow cover < 1 cm',
        '998': 'gebroken sneeuwdek/broken snow cover >=1 cm',
        '999': 'sneeuwhopen/snow dunes}',
        }
    SNOWVALS = {'997':'1','998':'1','999':'1'}
    SKIPROWS = 24

    def __init__(self,fpath):

        self.colnames = self.NAMESTR.replace(' ','').split(',')
        # NAMESTR[:-1] : trailing colon creates extra column
        self.keepcols = self.colnames
        self.fpath = Path(fpath)

        if not (self.fpath.exists() and self.fpath.is_file()):
            msg = [f'Filepath \'{self.fpath}\' not found',
                'empty dataframe is returned.']
            warnings.warn(' '.join(msg))
            self.rawdata = pd.DataFrame(columns=self.colnames)
            self.data = pd.DataFrame(columns=self.keepcols)
        else:
            self._readfile()
            self._clean_rawdata()


    def _readfile(self):

        # read csv to pd.DataFrame with only str values
        self.rawdata = pd.read_csv(self.fpath,sep=',',
            skiprows=self.SKIPROWS,
            names=self.colnames,dtype='str')

        # replace empty strings with NaN
        self.rawdata = self.rawdata.apply(
            lambda x: x.str.strip()).replace('', np.nan)


    def _clean_rawdata(self):

        self.data = self.rawdata[self.keepcols].copy()
        for colname in list(self.data):

            if colname=='YYYYMMDD':
                self.data[colname] = pd.to_datetime(self.data[colname],
                    infer_datetime_format=True)
                self.data = self.data.set_index(
                    colname,verify_integrity=True)
                self.data.index.name='date'

            if colname=='RD':
                self.data[colname] = self.data[colname].astype(float)/10.

            if colname == 'SX':
                self.data[colname] = self.data[colname].replace(self.SNOWVALS)
                self.data[colname] = self.data[colname].astype(float)

            if colname == 'empty':
                self.data = self.data.drop(columns=[colname])


    def timeseries(self,varname):
        """Return timeseries with data

        Parameters
        ----------
        varname : {'prc')
            variable to return
        """
 
        if varname not in self.VARNAMES:
            msg = [f'{varname} is not a valid variable name.',
                f'parameter varname must be in {self.VARNAMES}',
                f'by default rain data are returned']
            warnings.warn(' '.join(msg))
            varname = 'prc'

        if varname == 'prc':
            sr = self.data['RD']
            sr.name = 'prc'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]


    def units(self):
        """Return table with definitions and units of variables"""

        tbl = pd.DataFrame({
            'variable' : ['prc','snow'],
            'datacol' : ['RH','EV24'],
            'unit' : ['mm/day','cm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl

