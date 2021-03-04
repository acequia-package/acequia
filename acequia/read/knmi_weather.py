
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


class KnmiWeather:
    """Read weather data from knmi file

    Parameters
    ----------
    fpath : str
        path to knmi txt file with weather data


    Examples
    --------

    wth = aq.KnmiWeather(<filepath>)

    evp = wth.timeseries('evp')

    name = wth.name()


    """

    NAMESTR = ''.join([
        'STN,YYYYMMDD,DDVEC,FHVEC,   FG,  FHX, FHXH,  FHN, FHNH,',
        '  FXX, FXXH,   TG,   TN,  TNH,   TX,  TXH, T10N,T10NH,   SQ,',
        '   SP,    Q,   DR,   RH,  RHX, RHXH,   PG,   PX,  PXH,   PN,',
        '  PNH,  VVN, VVNH,  VVX, VVXH,   NG,   UG,   UX,  UXH,   UN,',
        '  UNH, EV24'])

    VARNAMES = ['prc','evp','rch']

    SKIPROWS = 48

    def __init__(self,fpath):


        self.colnames = self.NAMESTR.replace(' ','').split(',')
        self.keepcols = 'YYYYMMDD,RH,EV24'.split(',')
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


        self.stn = self.rawdata.loc[0,'STN']


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

                # create datetimeindex from string column
                self.data[colname] = pd.to_datetime(self.data[colname],
                    infer_datetime_format=True)
                self.data = self.data.set_index(
                    colname,verify_integrity=True)

                # make sure all dates are in index
                firstdate = self.data.index[0]
                lastdate = self.data.index[-1]
                idx = pd.date_range(start=firstdate, end=lastdate,
                    freq='D')
                self.data = self.data.reindex(idx)
                self.data.index.name='date'

            if colname=='RH':
                # RH is precipitation in 0.1 mm/day
                # RH = -1 means RH < 0.05 mm/day
                self.data[colname] = self.data[colname].replace('-1','0.5')

            if colname in ['RH','EV24']:
                self.data[colname] = self.data[colname].astype(float)/10.


    def timeseries(self,varname):
        """Return timeseries with data

        Parameters
        ----------
        varname : {'prc','evp','rch')
            variable to return
        """
 
        if varname not in self.VARNAMES:
            msg = [f'{varname} is not a valid variable name.',
                f'parameter varname must be in {self.VARNAMES}',
                f'by default rain data are returned']
            warnings.warn(' '.join(msg))
            varname = 'prc'

        if varname == 'prc':
            sr = self.data['RH']
            sr.name = 'prc'
        if varname == 'evp':
            sr = self.data['EV24']
            sr.name = 'evp'
        if varname == 'rch':
            sr = self.data['RH']-self.data['EV24']
            sr.name = 'rch'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]


    def units(self):
        """Return table with definitions and units of variables"""

        tbl = pd.DataFrame({
            'variable' : ['prc','evp','rch'],
            'datacol' : ['RH','EV24','calculated'],
            'unit' : ['mm/day','mm/day','mm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl


