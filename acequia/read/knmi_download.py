""" 
Defines the KnmiLocations class that returns a list of available KNMI stations on the KNMI website and creates tables with station numbers 
and names.

Example
-------
>>> stations = aq.knmilocations()

"""

import os,os.path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import warnings
import requests
import pkgutil
from io import StringIO
import warnings
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import pandas as pd
from json import JSONDecodeError

from ..geo.coordinate_conversion import CrdCon
##from ..data.knmi_data import knmi_prc_coords

def knmilocations(stntype='prc'):
    """ Return table with KNMI stations.
    
    Parameters
    ----------
    stntype : {'prc','wtr'}, default 'prc'
        type of knmi station

    Returns
    -------
    pd.DataFrame

    """

    knmi = KnmiDownload()

    if stntype not in ['prc','wtr',]:
        warnings.warn((f'Invalid stntype {stntype}. Default "prc" '
            f'will be used.'))
        stntype='prc'
    
    if stntype=='prc':
        tbl = knmi.prc_stns

    if stntype=='wtr':
        tbl = knmi.wtr_stns

    return tbl


class KnmiDownload:
    """Retrieve KNMI list of all available station numbers and names
    from KNMI website 

    Methods
    -------
    prc_stns(filepath=None)
        return list of manual rain gauche locations

    wtr_stns(filepath=None)
        return list of weather station locations

    Note
    ----
    Downloading lists of KNMI stations from the website takes time. 
    Recommended use is to download these data only once and save 
    results as csv for further use.

    """
    WEATHER_URL=r'https://www.daggegevens.knmi.nl/klimatologie/daggegevens'
    PRECIPITATION_URL=r'https://www.daggegevens.knmi.nl/klimatologie/monv/reeksen'
    BACKSHIFT = 2 #Backshift in months from today for retrieving one day of data

    WEATHER_HEADERLINE = '# STN         LON(east)   LAT(north)  ALT(m)      NAME'
    PRC_HEADERLINE = '# STN         NAME'

    #STN_COLS = ['stn_name','stn_type','xcr','ycr','lon','lat','alt']
    #STN_INDEXNAME = 'stn_nr'

    def __init__(self):

        # read list of precipitation station coordinates from 
        # local csv file within package
        #self.prc_crd = knmi_prc_coords()
        pass

    def __repr__(self):
        return self.__class__.__name__

    def _request_weather(self,par=None):
        """Request weather data and return server response."""

        if par is None:
            par = {
                'start':'20090817',
                'end':'20090817',
                'stns':'260',
                'vars':'RH:EV24',
                'fmt':'json'}

        # make actual request to knmi server
        self._response = requests.get(self.WEATHER_URL,params=par) 
        self._response_code = self._response.status_code
        self._response_url = self._response.url
        return self._response

    def _request_precipitation(self,par=None):
        """Request precipitation data and return server response."""

        if par is None:
            par = {
                'start':'20090817',
                'end':'20090817',
                'stns':'330',
                'fmt':'json'}

        # make actual request to knmi server
        self._response = requests.get(self.PRECIPITATION_URL,params=par) 
        self._response_code = self._response.status_code
        self._response_url = self._response.url
        return self._response


    def download(self,kind='weather',start=None,end=None,stns=None,vars=None,
        result='data'):
        """Download KNMI weather station data.

        Parameters
        ----------
        kind : {'weather','prc'}, default 'weather'
            Measurement station type.
        start : str, optional (default yesterday)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).
        stns : str or list of str (default all)
            Numbers of stations to download.
        vars : str, optional (default 'RH:EV24')
            Measured variables to download.
        result : {'data',text'}, default 'data'
            Output type.

        Returns
        -------
        Dataframe (data) or List of str (text)

        Notes
        -----
        With parameter output 'text' a list of strings is retured. This
        response is equal to the csv files that can be downloaded manually 
        from the KNMI website, including a large header with explanation
        of measured paramters. With parameter output 'data' a DataFrame
        with data is returned.
        """
        if kind not in ['weather','prc']:
            warnings.warn((f"Invalid measurement station type {kind}. "
                f"Default station type 'weather' is returned."))
            kind = 'weather'

        if result not in ['data','text']:
            warnings.warn((
                f"Invalid result parameter {result}. Data is returned."))
            result = 'json'

        # set request parameters
        if start is None:
            # publishing measurements can take asom time
            startday = (datetime.today()-relativedelta(
                months=self.BACKSHIFT))
            start = startday.strftime('%Y%m%d')
        if end is None:
            ##start_day = datetime.strptime(start, '%Y%m%d') #+timedelta(days=1)
            end = start

        if (stns is None) & (kind=='weather'):
            stns = '260' #'all'
        if (stns is None) & (kind=='prc'):
            stns = '330'

        fmt = 'çsv'
        if result=='data':
            fmt = 'json'

        # request data from server
        par = {'start':start,'end':end,'stns':stns,'fmt':fmt}
        if kind=='weather':
            if vars is None:
                vars = 'RH:EV24'
            par['vars']=vars
            response = self._request_weather(par=par)
        if kind=='prc':
            response = self._request_precipitation(par=par)

        # parse server response
        data = response.text #.splitlines()
        if fmt=='json':
            # parse result tp json
            try:
                data = response.json()
                data = DataFrame(data)
            except JSONDecodeError as err:
                raise JSONDecodeError((f'Response could not be serialised '
                    f'with request  {self._response_url}.'))
            if data.empty:
                warnings.warn((f'No data available for station {stns} '
                    f'inperiod {start} - {end}.'))

        return data


    def _findline(self,lines=None,tagline=None):
        """Find linenr of line in lines."""
        for i,line in enumerate(lines):
            if line.startswith(tagline):  
                start = i+1
                break
        if start is None:
            raise ValueError(f'Tagline not found: {tagline}.')
        return start

    def _find_first_non_numeric_line(self,lines=None,start=None):

        for j in range(start,len(lines)-1):
            line = lines[j]
            starts_with_number = line[1:9].strip().isnumeric()

            if not starts_with_number:
                end = j
                break
        return end

    @property
    def wtr_stns(self):
        """Return table of all available KNMI weather stations."""


        # download metadata for all weather stationa
        text = self.download(kind='weather',start=None,end=None,stns='all', #'260',
            vars=None,result='text')
        lines = text.splitlines()

        # find startline
        start = self._findline(lines=lines,tagline=self.WEATHER_HEADERLINE)

        # find endline
        end = self._find_first_non_numeric_line(lines=lines,start=start)

        # table stn numbers and metadata
        wht_stn=[]
        for i in range(start,end):

            parts = lines[i].split()
            name = ' '.join(parts[5:]) # 'De Bilt' was split...
            rec = {
                'stn':int(parts[1]),
                'lon':parts[2],
                'lat':parts[3],
                'alt':parts[4],
                'name':name,
                }
            wht_stn.append(rec)

        return DataFrame(wht_stn).set_index('stn')

    @property
    def prc_stns(self):
        """ Return table of all available precipitation stations on KNMI site

        Notes
        -----
        Coordinates of precipitation stations are not available on the
        KNMI website.
        """

        text = self.download(kind='prc',stns='all',result='text')
        lines = text.splitlines()

        # find startline
        start = self._findline(lines=lines,tagline=self.PRC_HEADERLINE)

        # find endline
        end = self._find_first_non_numeric_line(
            lines=lines,start=start)

        # table stn numbers and metadata
        prc_stn=[]
        for i in range(start,end):

            parts = lines[i].split()
            name = ' '.join(parts[2:]) # 'De Bilt' was split...
            rec = {
                'stn':int(parts[1]),
                'name':name,
                }
            prc_stn.append(rec)

        return DataFrame(prc_stn).set_index('stn')

