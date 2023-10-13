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
import logging
import requests
import pkgutil
import pkg_resources
from io import StringIO
import warnings
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import pandas as pd
import geopandas as gpd
from json import JSONDecodeError
from .._geo.coordinate_conversion import CrdCon

logger = logging.getLogger(__name__)

def get_knmi_weatherstations(geodataframe=True):
    """ Return table of KNMI weather stations."""

    # download table of weather stations
    knmi = KnmiDownload()
    stns = knmi.weather_stations
    stns['label'] = stns.index.astype(str) + '_' + stns['stn_name']

    if geodataframe is True:
        # return GeoDataFrame
        stns = gpd.GeoDataFrame(
            stns, geometry=gpd.points_from_xy(stns.lon, stns.lat))
        stns = stns.set_crs('epsg:4326')
        stns = stns.to_crs('epsg:28992')
    else:
        # return just locations ids and names
        stns = stns[['stn_name']] 

    return stns

def get_knmi_precipitationstations(geodataframe=True):
    """ Return table of KNMI precipitation stations.
    
    Parameters
    ----------
    geodataframe : bool, default True
        Return GeoDataframe (True) or DataFrame (False)

    Returns
    -------
    GeoDataFrame, DataFrame
    
    Notes
    -----
    Coordinates of precipitation stations are not available from 
    the KNMI website. Instead, a local file with approximate 
    coordinates is used. To get a list of current KNMI precipitation 
    stations from the KNMI website without coordinates, use this 
    function with parameter geodataframe=False.
       
    """

    if not geodataframe:
        # download list from KNMI website
        knmi = KnmiDownload()
        return knmi.precipitation_stations

    if geodataframe:
        # "stream" is a stream-like object. If you want the actual info, call
        # stream.read()
        fpath = 'knmi_precipitation_coords.csv'
        stream = pkg_resources.resource_stream(__name__, fpath)
        stns =  pd.read_csv(stream, encoding='latin-1')

        stns['label'] = stns['stn_nr'].astype(str)+'_'+stns['stn_name']
        stns = stns.set_index('stn_nr')
        stns = gpd.GeoDataFrame(
            stns, geometry=gpd.points_from_xy(stns.xcrd, stns.ycrd))
        stns = stns.set_crs('epsg:28992')
    return stns


def get_knmiprec(station='327', location=None, start=None, end=None):
    """Return data from KNMI precipitation station.
    
    Parameters
    ----------
    station : str (default '327')
        Identification code of KNMI precipitation station.
    location : str, default None
        Name of KNMI location.
    start : str, optional (default january first of current year)
        First day of download period (format as %Y%m%d).
    end : str, optional (default today)
        Last day of download period (format as %Y%m%d).

    Returns
    -------
    pd.Series

    Notes
    -----
    KNMI precipitation stations are identified by their identification 
    (parameter "station", i.e. "327"). The parameter "location" allows 
    identification by location name (i.e. "Dwingelo").
       
    """
    knmi = KnmiDownload()
    sr = knmi.get_precipitation(station=station, location=location, start=start, end=end)
    return sr

def get_knmiweather(station='260', location=None, start=None, end=None,):
    """Return precipitation and evaporation from KNMI weather station.

    Parameters
    ----------
    station : str (default '260'), optional
        Identification code of KNMI weather station.
    location : str, optional
        Name of KNMI weather station.
    start : str, optional (default january first of current year)
        First day of download period (format as %Y%m%d).
    end : str, optional (default today)
        Last day of download period (format as %Y%m%d).

    Returns
    -------
    pd.DataFrame

    Notes
    -----
    KNMI weather stations are identified by their identification (parameter 
    "station", i.e. "260"). The parameter "location" allows identification
    by location name (i.e. "De Bilt").
       
    """
    knmi = KnmiDownload()
    data = knmi.get_weather(station=station, location=location, start=start, end=end)
    return data



class KnmiDownload:
    """Retrieve KNMI list of all available station numbers and names
    from KNMI website 

    Methods
    -------
    prec_stns(filepath=None)
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
    PREC_HEADERLINE = '# STN         NAME'

    def __init__(self):

        self._precstns = None
        self._wtrstns = None

    def __repr__(self):
        return self.__class__.__name__

    def _request_weather(self,par=None):
        """Request weather data and return server response."""

        if par is None: #this is for testing
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


    def download(self,kind='weather',start=None,end=None,stns='260',vars='RH:EV24',
        result='data'):
        """Download KNMI data and return dataframe with raw data.

        Parameters
        ----------
        kind : {'weather','prec'}, default 'weather'
            Measurement station type.
        start : str, optional (default january first of current year)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).
        stns : str or list of str (default '260')
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
        if kind not in ['weather','prec']:
            warnings.warn((f"Invalid measurement station type {kind}. "
                f"Default station type 'weather' is returned."))
            kind = 'weather'

        if result not in ['data','text']:
            warnings.warn((
                f"Invalid result parameter {result}. Data is returned."))
            result = 'json'

        # set request parameters
        if start is None:
            ## publishing measurements can take asom time
            ##startday = (datetime.today()-relativedelta(
            ##    months=self.BACKSHIFT))
            ##start = startday.strftime('%Y%m%d')
            thisyear = str(datetime.today().year)
            start = f'{thisyear}0101'
        if end is None:
            ##start_day = datetime.strptime(start, '%Y%m%d') #+timedelta(days=1)
            end = datetime.strftime(datetime.today(), '%Y%m%d')
        if isinstance(stns,list):
            stns = ':'.join(stns) # correct format is '260:279' for two stations

        # request data from server
        if result=='data':
            fmt = 'json'
        else:
            fmt = 'çsv' # result is text
        par = {'start':start,'end':end,'stns':stns,'fmt':fmt}
        if kind=='weather':
            par['vars']=vars
            response = self._request_weather(par=par)
        if kind=='prec':
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

    def _findline(self, lines=None, tagline=None, start=None):
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
    def weather_stations(self):
        """Return table of all available KNMI weather stations."""

        if self._wtrstns is not None: # were downloaded earlier
            return self._wtrstns

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
                'stn_nr':int(parts[1]),
                'lon':parts[2],
                'lat':parts[3],
                'alt':parts[4],
                'stn_name':name,
                }
            wht_stn.append(rec)

        self._wtrstns = DataFrame(wht_stn).set_index('stn_nr')
        return self._wtrstns

    @property
    def precipitation_stations(self):
        """ Return table of all available precipitation stations on KNMI site

        Notes
        -----
        Coordinates of precipitation stations are not available on the
        KNMI website.
        """
        if self._precstns is not None: # were downloaded earlier
            return self._precstns 
        
        # request precipitation data for one day to get header data 
        # with all station names
        dummydate = f'{str(datetime.now().year)}0101'
        text = self.download(kind='prec', stns='all', result='text', start=dummydate, end=dummydate)
        if 'Query Error' in text:
            raise ValueError('KNMI server responded with a query error message.')

        # find startline of station names
        lines = text.splitlines()
        start = self._findline(lines=lines, tagline=self.PREC_HEADERLINE)

        # find endline of station names
        end = self._find_first_non_numeric_line(
            lines=lines, start=start)

        # table stn numbers and metadata
        prec_stn=[]
        for i in range(start,end):

            parts = lines[i].split()
            stn = int(parts[1])
            name = ' '.join(parts[2:]) # 'De Bilt' was split...
            rec = {
                'stn_nr':stn,
                'stn_name':name,
                }
            prec_stn.append(rec)

        self._precstns = DataFrame(prec_stn).set_index('stn_nr')
        return self._precstns

    def get_precipitation(self, station='327', location=None, start=None, end=None):
        """Return precipitation data.

        Parameters
        ----------
        station : str (default '327'), optional
            Number of precipitation station to download.
        location : str, optional
            Name of KNMI location.
        start : str, optional (default january first of current year)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).

        Returns
        -------
        pd.Series

        Notes
        -----
        KNMI stations are identified by their identification (parameter 
        "station", i.e. "327"). The parameter "location" allows identification
        by location name (i.e. "Dwingelo").
           
        """

        # try to get station id from given station name
        if isinstance(location,str):
            prec_stns = self.precipitation_stations
            station_name = prec_stns[prec_stns['stn_name']==location]
            if not station_name.empty:
                station = str(station_name.index[0])
            else:
                #warnings.warn((f'{station_name} is not a valid KNMI '
                #    f'precipitation station name. Default station {station} '
                #    f'will be used.'))
                logger.warning(
                    f'{location} is not a valid KNMI precipitation '
                    f'station name. Default station {station} '
                    f'will be used.'
                    )


        # download raw data
        rawdata = self.download(kind='prec', start=start, end=start, stns=station)

        # return time series
        data = rawdata.drop_duplicates(subset='date')
        dates = pd.to_datetime(data['date'])
        prec = data['RD'].values/10
        sr = Series(data=prec, index=dates, name=station)
        sr.index = sr.index.tz_localize(None)
        return sr

    def get_weather(self, station='260', location=None, start=None, end=None,):
        """Return precipitation and evaporation from weather station.

        Parameters
        ----------
        station : str (default '260'), optional
            Number of precipitation station to download.
        location : str, optional
            Name of KNMI location.
        start : str, optional (default january first of current year)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).

        Returns
        -------
        pd.Series

        Notes
        -----
        KNMI stations are identified by their identification (parameter 
        "station", i.e. "327"). The parameter "location" allows identification
        by location name (i.e. "Dwingelo").
           
        """

        # try to get station id from given station name
        if isinstance(location,str):
            weather_stations = self.weather_stations
            station_name = weather_stations[weather_stations['stn_name']==location]
            if not station_name.empty:
                station = str(station_name.index[0])
            else:
                warnings.warn((f'{station_name} is not a valid KNMI '
                    f'precipitation station name. Default station {station} '
                    f'will be used.'))

        # download raw data
        rawdata = self.download(kind='weather',start=start,end=end,stns=station)
        #return rawdata

        # return cleaned data
        data = rawdata.drop_duplicates(subset='date')
        data['date'] = pd.to_datetime(data['date'])
        data = data[['date','RH','EV24']].set_index('date')
        data = data/10.
        data.index = data.index.tz_localize(None)
        data = data.rename(columns={'RH':'prec','EV24':'evap'})
        data = data.loc[data.first_valid_index():,:] #drop leading NaNs
        return data
