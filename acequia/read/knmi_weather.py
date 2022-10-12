
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
    wtr = KnmiWeather.from_file(<filepath>)
    evp = wtr.timeseries('evp')
    name = wtr.name()
    """
    NAMESTR = ''.join([
        'STN,YYYYMMDD,DDVEC,FHVEC,   FG,  FHX, FHXH,  FHN, FHNH,',
        '  FXX, FXXH,   TG,   TN,  TNH,   TX,  TXH, T10N,T10NH,   SQ,',
        '   SP,    Q,   DR,   RH,  RHX, RHXH,   PG,   PX,  PXH,   PN,',
        '  PNH,  VVN, VVNH,  VVX, VVXH,   NG,   UG,   UX,  UXH,   UN,',
        '  UNH, EV24'])
    COLNAMES = NAMESTR.replace(' ','').split(',')
    KEEPCOLS = 'YYYYMMDD,RH,EV24'.split(',')
    VARNAMES = ['prc','evp','rch']
    SKIPROWS = 52

    def __init__(self,rawdata=None,desc=None,fpath=None):
        """Use KnmiWeather.from_file(fpath) to construct from csv file 
        path."""
        self.fpath = fpath
        self.rawdata = rawdata
        self.desc = desc
        self.data = self._clean_rawdata(self.rawdata)
        self.stn = int(self.rawdata.loc[0,'STN'])

    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self.data)})')

    @classmethod
    def from_file(cls,filepath):
        """Read Knmi Weather csv file.
        
        Parameters
        ----------
        filepath : str
            Valid filepath to csv file with weather data.

        Returns
        -------
        pd.DataFrame
        """

        rawdata = pd.read_csv(filepath,sep=',',
            skiprows=cls.SKIPROWS,
            names=cls.COLNAMES,dtype='str')

        # replace empty strings with NaN
        rawdata = rawdata.apply(
            lambda x: x.str.strip()).replace('', np.nan)

        # read metadata from header
        with open(filepath, 'r') as fp:
            line_numbers = list(range(10,50))
            lines = []
            for i, line in enumerate(fp):
                if i in line_numbers:
                    line = line.strip()
                    desc = line[11:].strip()
                    rec = {
                        'variabele':line[0:10].strip(),
                        'omschrijving':desc.split('/')[0].strip(),
                        'description':desc.split('/')[1].strip(),
                        }
                    lines.append(rec)
                elif i > 49:
                    break
        desc = DataFrame(lines)

        return cls(rawdata=rawdata,desc=desc,fpath=filepath)


    def _clean_rawdata(self,rawdata):

        data = rawdata[self.KEEPCOLS].copy()
        for colname in list(data):

            if colname=='YYYYMMDD':

                # create datetimeindex from string column
                data[colname] = pd.to_datetime(data[colname], #,format='%Y%m%d')
                    infer_datetime_format=True)
                data = data.set_index(
                    colname,verify_integrity=True)

                # make sure all dates are in index
                firstdate = data.index[0]
                lastdate = data.index[-1]
                idx = pd.date_range(start=firstdate, end=lastdate,
                    freq='D')
                data = data.reindex(idx)
                data.index.name='date'

            if colname=='RH':
                # RH is precipitation in 0.1 mm/day
                # RH = -1 means RH < 0.05 mm/day
                data[colname] = data[colname].replace('-1','0.5')

            if colname in ['RH','EV24']:
                data[colname] = data[colname].astype(float)/10.

        # drop nans and reindex
        data = data.dropna(how='all')
        newindex = pd.date_range(data.index.min(),data.index.max())
        data = data.reindex(newindex)

        return data

    def timeseries(self,var='prc'):
        """Return timeseries with data

        Parameters
        ----------
        var : {'prc','evp','rch'), default 'prc'
            variable to return
            
        Returns
        -------
        pd.Series
        """
        if var not in self.VARNAMES:
            msg = [f'{var} is not a valid variable name.',
                f'parameter varname must be in {self.VARNAMES}',
                f'by default rain data are returned']
            warnings.warn((f'{var} is not a valid variable name. ',
                f'parameter varname must be in {self.VARNAMES}'
                f'by default rain data are returned.'))
            var = 'prc'

        if var == 'prc':
            sr = self.data['RH']
            sr.name = 'prc'
        if var == 'evp':
            sr = self.data['EV24']
            sr.name = 'evp'
        if var == 'rch':
            sr = self.data['RH']-self.data['EV24']
            sr.name = 'rch'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]

    @property
    def units(self):
        """Return table with definitions and units of variables"""
        tbl = pd.DataFrame({
            'variable' : ['prc','evp','rch'],
            'datacol' : ['RH','EV24','calculated'],
            'unit' : ['mm/day','mm/day','mm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl

    @property
    def prc(self):
        """Return precipitation time series."""
        return self.timeseries(var='prc')

    @property
    def evp(self):
        """Return evaporation time series."""
        return self.timeseries(var='evp')

    @property
    def recharge(self):
        """Return recharge time series."""
        return self.timeseries(var='rch')

