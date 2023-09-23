
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


class KnmiRain:
    """Read precipitation data from text file downloaded from KNMI website."""

    NAMESTR = 'STN,YYYYMMDD,   RD,   SX,' + 'empty'
    COLNAMES = NAMESTR.replace(' ','').split(',')
    KEEPCOLS = COLNAMES
    VARNAMES = ['prec','snow']
    SNOWCODE = {
        '997': 'gebroken sneeuwdek/broken snow cover < 1 cm',
        '998': 'gebroken sneeuwdek/broken snow cover >=1 cm',
        '999': 'sneeuwhopen/snow dunes}',
        }
    SNOWVALS = {'997':'1','998':'1','999':'1'}
    SKIPROWS = 24


    def __init__(self,filepath=None):
        """
        filepath : str
            Valid filepath to KNMI precipitation source file.
        """
        self.filepath = filepath
        self._fpath = Path(filepath)

        if not (self._fpath.exists() and self._fpath.is_file()):
            # return object with empty dataframes
            warnings.warn((f"Filepath '{self.filepath}' not found"
                'empty dataframe is returned.'))
            self.header = None
            self.rawdata = pd.DataFrame(columns=self.COLNAMES)
            self.data = pd.DataFrame(columns=self.KEEPCOLS)
        else:
            # read header data
            self.header = self._read_header(self._fpath)

            # read precipitation and snow
            self.rawdata = self._readfile(self._fpath)
            self.data = self._clean_rawdata(self.rawdata)


    def __repr__(self):
        ##stn = self.station if self.station is not None else ''
        ##loc = self.location if self.location is not None else ''
        ##return (f'{self.__class__.__name__} (n={len(self.data)})')
        return (f'{self.station} {self.location} ({self.period})')

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

                # remove duplicate dates
                duplicates = data[data.duplicated(subset='YYYYMMDD')]
                if not duplicates.empty:
                    warnings.warn((f'Removed {len(duplicates)} duplicate dates'
                        f' from {self.filepath}.'))
                    data = data.drop_duplicates(subset='YYYYMMDD', keep='first')

                # set date as index
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


    def get_timeseries(self,var='prec'):
        """Return timeseries with data

        Parameters
        ----------
        varname : {'prec','snow'), default 'prec'
            variable to return

        Returns
        -------
        pd.Series
        """

        if var not in self.VARNAMES:
            msg = []
            warnings.warn((f'{var} is not a valid variable name. '
                f'parameter var must be in {self.VARNAMES} '
                f'by default precipitation data are returned.'))
            varname = 'prec'

        if self.data.empty:
            return DataFrame()

        if var == 'prec':
            sr = self.data['RD']
            sr.name = 'prec'

        if var == 'snow':
            sr = self.data['SX']
            sr.name = 'snow'

        first = sr.first_valid_index()
        last = sr.sort_index(ascending=False).first_valid_index()
        return sr[first:last]


    @property
    def prec(self):
        """Return timeseries of daily precipitation measurements."""
        return self.get_timeseries('prec')

    @property
    def snow(self):
        """Return timeseries of daily precipitation measurements."""
        return self.get_timeseries('snow')

    @property
    def units(self):
        """Return table with definitions and units of variables"""
        tbl = pd.DataFrame({
            'variable' : ['prec','snow'],
            'datacol' : ['RH','EV24'],
            'unit' : ['mm/day','cm/day'], 
            })
        tbl = tbl.set_index('variable')
        return tbl

    @property
    def station(self):
        """Return station identification code."""
        if self.header is None:
            return None
        return self.header[6].split()[1]

    @property
    def location(self):
        """Return station location name."""
        if self.header is None:
            return None
        return self.header[6][5:-1].strip()

    @property
    def period(self):
        """Return precipitation measurment yearspan."""
        return f'{self.prec.index[0].year} - {self.prec.index[-1].year}'
