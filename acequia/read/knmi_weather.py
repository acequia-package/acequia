
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
    evap = wtr.timeseries('evap')
    name = wtr.name()
    """
    KEEPCOLS = ['YYYYMMDD','RH','EV24']
    VARIABLES = ['prec','evap','rch']
    SKIPROWS = 47

    def __init__(self,filepath=None):
        """Read Knmi Weather csv file.
        
        Parameters
        ----------
        filepath : str
            Valid filepath to csv file with weather data.
        """
        self.filepath = filepath
        self.header = self._read_header(filepath)
        self.rawdata = self._read_data(filepath)
        self.data = self._clean_rawdata(self.rawdata)
        ##self.stn = int(self.rawdata.loc[0,'STN'])

    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self.data)})')

    def _read_header(self, fpath):
        """Read headerlines from source file."""
        header = []
        with open(fpath) as f:
            while True:
                line = f.readline()
                if line.startswith('#'):
                    header.append(line[:-1]) # -1 : drop '\n'
                else:
                    break
        return header

    def _read_data(self,filepath):

        # extract column names from file header
        colnames = [x.strip() for x in self.header[-1][2:].split(',')]

        # read data with pandas
        rawdata = pd.read_csv(filepath,sep=',',
            skiprows=self.SKIPROWS,
            names=colnames,dtype='str')

        # replace empty strings with NaN
        rawdata = rawdata.apply(
            lambda x: x.str.strip()).replace('', np.nan)

        return rawdata

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

    def get_timeseries(self,var='prec'):
        """Return timeseries with data

        Parameters
        ----------
        var : {'prec','evap','rch'), default 'prec'
            variable to return
            
        Returns
        -------
        pd.Series
        """
        if var not in self.VARIABLES:
            warnings.warn((f'{var} is not a valid variable name. '
                f'parameter varname must be in {self.VARIABLES}'
                f'by default rain data are returned.'))
            var = 'prec'

        if var == 'prec':
            sr = self.data['RH']
            sr.name = 'prec'
        if var == 'evap':
            sr = self.data['EV24']
            sr.name = 'evap'
        if var == 'rch':
            sr = self.data['RH']-self.data['EV24']
            sr.name = 'rch'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]

    @property
    def variables(self):
        records = []
        for line in self.header[7:46]:
            records.append({
                'variabele' : line[1:].split(':')[0].strip(),
                'description' : line[14:].strip(),
                })
        return DataFrame(records).set_index('variabele')

    @property
    def units(self):
        """Return table with definitions and units of variables"""
        tbl = pd.DataFrame({
            'variable' : ['prec','evap','rch'],
            'datacol' : ['RH','EV24','RH-EV24'],
            'unit' : ['mm/day','mm/day','mm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl

    @property
    def prec(self):
        """Return precipitation time series."""
        return self.get_timeseries(var='prec')

    @property
    def evap(self):
        """Return evaporation time series."""
        return self.get_timeseries(var='evap')

    @property
    def recharge(self):
        """Return recharge time series."""
        return self.get_timeseries(var='rch')

    @property
    def station(self):
        """Return station identification code."""
        return self.header[6][2:5]

    @property
    def location(self):
        """Return station location name."""
        return self.header[6][49:].strip()

    @property
    def lon(self):
        """Return station location longitude."""
        return self.header[6][14:26].strip()

    @property
    def lat(self):
        """Return station location latitude."""
        return self.header[6][26:38].strip()

    @property
    def altitude(self):
        """Return station location altitude."""
        return self.header[6][38:50].strip()

