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
from shapely.geometry import Point
from geopandas import GeoSeries
import geopandas as gpd
from json import JSONDecodeError
from .._geo.coordinate_conversion import CrdCon, convert_WGS84toRD

logger = logging.getLogger(__name__)


def get_knmiwtr_stn(geo=False):
    """ Return KNMI weather stations.

    Parameters
    ----------
    geo : bool, default False
        Return geodataframe (True) or pandas DataFrame (default).

    Returns
    -------
    pandas DataFrame, geopandas GeoDataframe
        
    """
    knmi = KnmiDownload()
    if geo:
        stns = knmi.get_weather_stations(geo=True)
    else:
        stns = knmi.get_weather_stations(geo=False)

    return stns

def get_knmiprc_stn(geo=False):
    """ Return KNMI precipitation stations.
    
    Parameters
    ----------
    geo : bool, default False
        Return GeoDataframe (True) or DataFrame (False)

    Returns
    -------
    GeoDataFrame, DataFrame
       
    """
    if geo:
        knmi = KnmiDownload()        
        stns = knmi.get_precipitation_stations(geo=True)
    else:
        stns = knmi.get_precipitation_stations(geo=False)

    return stns


def get_knmiprc(station='327', name=None, start=None, end=None):
    """Return data from KNMI precipitation station.
    
    Parameters
    ----------
    station : str (default '327')
        Identification code of KNMI precipitation station.
    name : str, default None
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
    (parameter "station", i.e. "327"). The parameter "name" allows 
    identification by location name (i.e. "Dwingelo").
       
    """
    knmi = KnmiDownload()
    sr = knmi.get_precipitation(station=station, name=name, start=start, end=end)
    return sr

def get_knmiwtr(station='260', name=None, start=None, end=None,):
    """Return precipitation and evaporation from KNMI weather station.

    Parameters
    ----------
    station : str (default '260'), optional
        Identification code of KNMI weather station.
    name : str, optional
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
    "station", i.e. "260"). The parameter "name" allows identification
    by location name (i.e. "De Bilt").
       
    """
    knmi = KnmiDownload()
    data = knmi.get_weather(station=station, name=name, start=start, end=end)
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
    DEFAULT_PREC = '327'
    DEFAULT_WTR = '260'
    WEATHER_HEADER_FIRSTLINE = '# STN         LON(east)   LAT(north)  ALT(m)      NAME'
    WEATHER_HEADER_STOPLINE = '# RH        : Etmaalsom van de neerslag (in 0.1 mm)'
    PREC_HEADER_FIRSTLINE = '# STN         NAME'
    PREC_HEADER_STOPLINE = '# RD        : 24-uur som van de neerslag'
    MINIMAL_REPLACEMENTS = 3

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

        if par is None: #this is for testing
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


    def get_rawdata(self, kind='weather', stns='260', start=None, end=None,
        variables='RH:EV24', result='data'):
        """Download KNMI data and return dataframe with raw data.

        Parameters
        ----------
        kind : {'weather','precipitation'}, default 'weather'
            Measurement station type.
        stns : str or list of str (default '260')
            Numbers of stations to download.
        start : str, optional (default january first of current year)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).
        variables : str, optional (default 'RH:EV24')
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
        if kind not in ['weather','precipitation']:
            raise ValueError((f"Invalid measurement station type {kind}. "))

        if result not in ['data','text']:
            warnings.warn((
                f"Invalid result parameter {result}. Data is returned."))
            result = 'json'

        # set request parameters
        if start is None:
            thisyear = str(datetime.today().year)
            start = f'{thisyear}0101'
        if end is None:
            end = datetime.strftime(datetime.today(), '%Y%m%d')
        if isinstance(stns,list):
            stns = ':'.join(stns) # correct format is '260:279' for two stations

        # set reponse data format
        if result=='data':
            fmt = 'json'
        else:
            fmt = 'çsv' # result is text
        par = {'start':start,'end':end,'stns':stns,'fmt':fmt}

        # request data from server
        if kind=='weather':
            par['vars']=variables
            self._response = self._request_weather(par=par)
        if kind=='precipitation':
            self._response = self._request_precipitation(par=par)

        # parse server response
        data = self._response.text
        if fmt=='json':
            # parse result tp json
            try:
                data = self._response.json()
                data = DataFrame(data)
            except JSONDecodeError as err:
                raise JSONDecodeError((f'Response could not be serialised '
                    f'with request  {self._response_url}.'))
            ##if data.empty:
            ##    warnings.warn((f'No data available for station {stns} '
            ##        f'inperiod {start} - {end}.'))
        return data

    def _findline(self, lines=None, tagline=None, start=None):
        """Find linenr of line in lines."""
        for i,line in enumerate(lines):
            if line.startswith(tagline):  
                line_nr = i
                break
        if line_nr is None:
            raise ValueError(f'Tagline not found: {tagline}.')
        return line_nr


    def get_weather_stations(self, geo=False):
        """Return table of KNMI Weather stations.
        
        Parameters
        ----------
        geo : bool, default False
            Return geodataframe (True) or pandas DataFrame (default).

        Returns
        -------
        pandas DataFrame, geopandas GeoDataframe
            
        """
        stns = self._wtrstn_hydropandas

        if geo:
            stns['label'] = stns.index + '_' + stns['stn_name']
            stns = gpd.GeoDataFrame(
                stns, geometry=gpd.points_from_xy(stns.xrd, stns.yrd))
            #stns = stns.set_crs('epsg:4326')
            #stns = stns.to_crs('epsg:28992')
            stns = stns.set_crs('epsg:28992')
        return stns

    #@property
    def get_precipitation_stations(self, geo=False):
        """Return table of KNMI precipitation stations.
        
        Parameters
        ----------
        geo : bool, default False
            Return geodataframe (True) or pandas DataFrame (default).

        Returns
        -------
        pandas DataFrame, geopandas GeoDataframe
            
        """
        stns = self._prcstn_hydropandas
        if geo:
            stns['label'] = stns.index + '_' + stns['stn_name']
            stns = gpd.GeoDataFrame(stns, 
                geometry=gpd.points_from_xy(stns.xrd, stns.yrd))
            stns = stns.set_crs('epsg:28992')
        else:
            pass
        return stns


    def get_precipitation(self, station=None, name=None, start=None, 
        end=None, kind='precipitation', fillnans=True):
        """Return precipitation data.

        Parameters
        ----------
        station : str, optional
            Number of precipitation station to download.
        name : str, optional
            Name of KNMI location.
        start : str, optional (default january first of current year)
            First day of download period (format as %Y%m%d).
        end : str, optional (default today)
            Last day of download period (format as %Y%m%d).
        kind : {'precipitation','weather'}, default 'precipitation'
            KNMI station type to get data from.
        fillnans : bool, default True
            Replace missing values with average values from three nearest
            stations.

        Returns
        -------
        pd.Series

        Notes
        -----
        KNMI stations are identified by their identification (parameter 
        "station", i.e. "327"). The parameter "name" allows identification
        by location name (i.e. "Dwingelo").
           
        """
        if kind not in ['weather','precipitation']:
            raise ValueError((f"Invalid measurement station type {kind}. "))

        if (station is None) & (name is None):
            raise ValueError((f'Either station code or station name must be given.'))


        if isinstance(name, str):
            # try to get station id from given station name
            station = self.get_station_code(name=name, kind=kind)
            if station is None:
                raise ValueError((f'{name} is not a valid KNMI '
                    f'{kind} station name.'))

            """
            # get table of station numbers and names
            if kind=='precipitation':
                stns = self.get_precipitation_stations()
            elif kind=='weather':
                stns = self.get_weather_stations()
            else:
                raise ValueError((f'{kind} is not a valid KNMI station type.'))

            # get station code from location name
            mask = stns['stn_name'].str.lower().str.contains(name.lower())
            if not stns[mask].empty:
                station = stns[mask].index[0]
            else:
                raise ValueError((f'{name} is not a valid KNMI '
                    f'{kind} station name.'))
            """

        # download raw data
        rawdata = self.get_rawdata(kind=kind, stns=station, start=start, end=end)

        # return time series of precipitation values

        sr = Series(name=station, dtype='object')
        #if rawdata.empty:
        #    return sr

        if kind=='precipitation':
            colname='RD'
            if not rawdata[~rawdata[colname].isnull()].empty:
                sr = rawdata[['date',colname]].copy()
                sr = sr.drop_duplicates(subset='date')
                dates = pd.to_datetime(sr['date'])
                prec = sr[colname].values/10
                sr = Series(data=prec, index=dates, name=station)
                sr.index = sr.index.tz_localize(None)
                sr = sr[sr.first_valid_index():] #drop leading nans

        if kind=='weather':
            colname='RH'
            if not rawdata[~rawdata[colname].isnull()].empty:
                data = rawdata[['date',colname]].copy()
                data = data.drop_duplicates(subset='date')
                dates = pd.to_datetime(data['date'])
                prec = data[colname].replace(-1,0).values/10. # -1 is used voor less then 0.5 mm percipitation
                sr = Series(data=prec, index=dates, name=station)
                sr.index = sr.index.tz_localize(None)


        # replace missing values
        if fillnans & (not sr.empty):
            sr,_ = self.replace_missing_values(meteo=sr, kind=kind)

        return sr


    def get_station_code(self, name=None, kind='precipitation'):
        """Return code of KNMI station with given name.
        Return None if name is not a valid KNMI station name.
        
        Parameters
        ----------
        name : str
            KNMI station name.
        kind : {'precipitation', 'weather'}, default 'precipitation'
            KNMI station type.

        Returns
        -------
        string or None
           
        """

        if kind=='precipitation':
            stns = self.get_precipitation_stations(geo=False)
            kindname = 'precipitation'
        elif kind=='weather':
            stns = self.get_weather_stations(geo=False)
            kindname = 'weather'
        else:
            raise ValueError((f'{kind} is not a valid KNMI sation type.'))

        station = stns[stns['stn_name']==name]
        if not station.empty:
            stn = station.index[0]
        else:
            ##raise ValueError((f'{name} is not a valid KNMI '
            ##    f'{kindname} station name.'))
            stn = None

        return stn


    def get_station_metadata(self, stn=None, kind='precipitation'):
        """Get KNMI station metadata from station code.

        Parameters
        ----------
        stn : str
            Valid KNMI station code.
        kind : {'precipitation', 'weather'}, default 'precipitation'
            KNMI station type.

        Returns
        -------
        str or None
            
        """
        if stn is None:
            raise ValueError((f'A valid KNMI stadfion code must be given.'))

        if kind not in ['weather','precipitation']:
            raise ValueError((f"Invalid measurement station type {kind}. "))

        if kind=='weather':
        
            stations = self.get_weather_stations()
            stations.insert(0,stations.index.name,stations.index)
            try:
                meta = stations.loc[stn,:].squeeze()
            except KeyError:
                meta = Series(dtype='object')

        if kind=='precipitation':

            stations = self.get_precipitation_stations()
            stations.insert(0,stations.index.name, stations.index)
            try:
                meta = stations.loc[stn,:].squeeze()
            except KeyError:
                meta = Series(dtype='object')

        # create series with metadata
        if not meta.empty:
            meta['stn_kind'] = kind
            meta.name = meta['stn_name']

        return meta


    def get_weather(self, station='260', name=None, start=None, end=None,
        fillnans=True):
        """Return precipitation and evaporation from weather station.

        Parameters
        ----------
        station : str (default '260'), optional
            Number of precipitation station to download.
        name : str, optional
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
        "station", i.e. "327"). The parameter "name" allows identification
        by name name (i.e. "Dwingelo").
           
        """

        if isinstance(name, str):
            # try to get station id from given station name
            station = self.get_station_code(kind='weather', name=name)

        # download raw data
        rawdata = self.get_rawdata(kind='weather', stns=station, start=start, end=end,
            variables='RH:EV24', result='data')

        # return cleaned data
        data = rawdata.drop_duplicates(subset='date')
        data['date'] = pd.to_datetime(data['date'])
        data = data[['date','RH','EV24']].set_index('date')
        data.index = data.index.tz_localize(None)
        data = data.rename(columns={'RH':'prec','EV24':'evap'})
        data = data.loc[data.first_valid_index():,:] # drop leading rows with only NaN
        data = data.loc[:data.last_valid_index(),:] # drop trailing rows with only NaN

        data['prec'] = data['prec'].replace(-1,0) # -1 is used voor less then 0.5 mm percipitation
        data = data/10.

        return data


    def get_distance(self, kind='precipitation', stn=None, name=None, xy=None, latlon=None):
        """Return table of distances between KNMI stations and a 
        reference point. Reference point can be given as a KNMI station 
        (station code or station name) or a coordinate (Dutch grid xy or
        WGS84 latlon).

        Parameters
        ----------
        kind : {'precipitation','weather'}, default 'precipitation'
            KNMI station type.
        stn : str, optional
            Valid KNMI station code.
        name : str, optional
            Valid KNMI station name.
        xy : tuple, optional
            Reference point coordinates as (xcoor, ycoor) in Dutch grid.
        latlon : tuple, optional
            Reference point coordinates as (lat, lon) in WGS84.

        Returns
        -------
        pandas DataFrame
            Table of KNMI stations with distance from reference point.
            
        """

        # determine data type : weather or precipitation
        if kind=='precipitation':
            stns = self.get_precipitation_stations(geo=True)
            kindname = 'precipitation'
            if isinstance(name, str):
                stn = self.get_station_code(kind='precipitation', name=name)

        elif kind=='weather':
            stns = self.get_weather_stations(geo=True)
            kindname = 'weather'
            if isinstance(name, str):
                stn = self.get_station_code(kind='weather', name=name)

        else:
            raise ValueError((f'{kind} is not a valid KNMI station type.'))

        if (stn not in stns.index.values) & (stn is not None):
            raise ValueError((f'{stn} is not a valid KNMI {kindname} station code.'))

        # get reference point coordinates as GeoSeries
        if stn:
            loc = stns.loc[stn,'geometry']
        if latlon:
            xy = convert_WGS84toRD(latlon[0],latlon[1])
        if xy:
            # exapend point to geoseries with index equal to stn
            # because geopandas .distance() method is index based
            data = [Point(xy[0], xy[1]) for x in range(len(stns))]
            index = stns.index
            loc = GeoSeries(data=data, index=index, crs='epsg:28992')

        # calculate distance in km to reference point for each station
        dist = stns.distance(loc)
        dist = (dist/1000.).round(0)
        dist.name = 'distance_km'

        # merge station names with calculated distance
        stns = pd.merge(stns[['stn_name']], dist, left_index=True, right_index=True, how='left')
        stns = stns.sort_values('distance_km')
        
        return stns

    def replace_missing_values(self, meteo=None, kind='precipitation'):
        """Replace missing values in a series of precipitation values.
        
        Parameters
        ----------
        meteo : pandas Series
            Time series with precipitation or evaporation values.
        kind : {'precipitation', 'weather'}, default 'precipitation'
            KNMI station type to get replacement values from.

        Returns
        -------
        pandas Series
            Copy of meteo with missing values replaced.
        pandas DataFrame
            Table of measurements used for replacement of missing values.
        """

        nandates = meteo[meteo.isnull()].index
        if nandates.empty: # no missing values
            return meteo.copy(), DataFrame()
        
        first_nan_date = nandates[0]
        last_nan_date = nandates[-1]

        # get codes of replecement stations
        dist = self.get_distance(kind=kind, stn=meteo.name)
        stn_codes = dist[dist['distance_km']!=0].index.values

        data = []
        for stn in stn_codes:
            try:
                sr = self.get_precipitation(kind=kind, station=stn, start=first_nan_date, end=last_nan_date)
                sr = sr[nandates]
            except KeyError:
                # not all nandates are in index of sr (non-overlapping time series)
                continue
            else:
                if not sr[~sr.isnull()].empty:
                    data.append(sr)
                if len(data)>=self.MINIMAL_REPLACEMENTS: # at least three new series
                    self._nan_replacements = pd.concat(data, axis=1)                
                    self._nan_replacements['mean'] = self._nan_replacements.mean(axis=1).round(0)
                    self._nan_replacements['n'] = self._nan_replacements.count(axis=1)-1

                    no_nans_left = self._nan_replacements[self._nan_replacements['mean'].isnull()].empty
                    enough_values = np.all(self._nan_replacements['n']>=self.MINIMAL_REPLACEMENTS)
                    if no_nans_left & enough_values:
                        newmeteo = meteo.copy()
                        newmeteo[self._nan_replacements.index] = self._nan_replacements['mean']
                        break

        return newmeteo, self._nan_replacements


    @property
    def _prcstn_hydropandas (self):
        """Return knmi precipitation station coordinates from hydropandas json file."""
        stream = pkg_resources.resource_stream(__name__, 'hydropandas_knmi_neerslagstation.json')
        stn = pd.read_json(stream, encoding='latin-1')
        
        stn.index = stn.index.astype('str').str.zfill(3)
        stn.index.name = 'stn_code'
        stn = stn.rename(columns={'naam':'stn_name', 'x':'xrd', 'y':'yrd', 'hoogte':'alt_mnap'})
        stn = stn[['stn_name','xrd','yrd','lat','lon','alt_mnap']].copy()
        return stn

    @property
    def _wtrstn_hydropandas(self):
        """Return knmi precipitation station coordinates from hydropandas json file."""
        stream = pkg_resources.resource_stream(__name__, 'hydropandas_knmi_meteostation.json')
        stn =  pd.read_json(stream, encoding='latin-1')

        stn.index = stn.index.astype('str').str.zfill(3)
        stn.index.name = 'stn_code'
        stn = stn.rename(columns={'naam':'stn_name', 'x':'xrd', 'y':'yrd', 'hoogte':'alt_mnap'})
        stn = stn[['stn_name','xrd','yrd','lat','lon','alt_mnap']].copy()
        return stn

    @property
    def _prcstn_acequia(self):
        """Return knmi precipitation station coordinates from acequia csv file."""

        # "stream" is a stream-like object. If you want the actual info, call
        # stream.read()
        fpath = 'knmi_precipitation_coords.csv'
        stream = pkg_resources.resource_stream(__name__, fpath)
        stns =  pd.read_csv(stream, encoding='latin-1')

        stns['stn_code'] = stns['stn_code'].astype('str').str.zfill(3)
        stns = stns.set_index('stn_code')
        return stns.sort_values(by='stn_name')


    @property
    def _prcstn_knmidownload(self):
        """Return table of all available precipitation stations on KNMI site

        Notes
        -----
        Coordinates of precipitation stations are not available on the
        KNMI website.
        """
        #if self._precstns is not None: # were downloaded earlier
        #    return self._precstns 
        
        # request precipitation data for one day to get header data 
        # with all station names
        dummydate = f'{str(datetime.now().year)}0101'
        text = self.get_rawdata(kind='precipitation', stns='all', result='text', start=dummydate, end=dummydate)
        if 'Query Error' in text:
            raise ValueError('KNMI server responded with a query error message.')

        # find startline of station names
        lines = text.splitlines()
        start = self._findline(lines=lines, tagline=self.PREC_HEADER_FIRSTLINE) + 1
        end = self._findline(lines=lines, tagline=self.PREC_HEADER_STOPLINE)

        # find endline of station names
        #end = self._find_first_non_numeric_line(
        #    lines=lines, start=start)

        # table stn numbers and metadata
        prec_stn=[]
        for i in range(start,end):

            parts = lines[i].split()
            stn = parts[1][:3] # [:3] because there is one line "# 427\t1       Voorschoten "
            name = ' '.join(parts[2:]) # 'De Bilt' was split...
            rec = {
                'stn_code':stn.zfill(3),
                'stn_name':name,
                }
            prec_stn.append(rec)

        precstns = DataFrame(prec_stn).set_index('stn_code')
        return precstns.sort_values(by='stn_name')
        
    @property
    def _wtrstn_knmidownload(self):
        """Return table of all available KNMI weather stations from knmi site."""

        #if self._wtrstns is not None: # stations were downloaded earlier
        #    return self._wtrstns

        # download metadata for all weather stationa
        dummydate = f'{str(datetime.now().year)}0101'

        text = self.get_rawdata(kind='weather', stns='all', result='text', 
            start=dummydate, end=dummydate, variables='RH:EV24')
        lines = text.splitlines()

        # find startline
        start = self._findline(lines=lines,tagline=self.WEATHER_HEADER_FIRSTLINE) + 1
        end = self._findline(lines=lines,tagline=self.WEATHER_HEADER_STOPLINE)

        # find endline
        ##end = self._find_first_non_numeric_line(lines=lines,start=start)

        # table stn numbers and metadata
        wht_stn=[]
        for i in range(start,end):

            parts = lines[i].split()
            name = ' '.join(parts[5:]) # 'De Bilt' was split...
            rec = {
                'stn_code' : parts[1].zfill(3),
                'stn_name' : name,
                'lat' : float(parts[3]),
                'lon': float(parts[2]),
                'alt_mnap' : float(parts[4]),
                }
            wht_stn.append(rec)

        # add coordinates in Dutch RD grid
        wtr_stns = DataFrame(wht_stn).set_index('stn_code')
        x, y = convert_WGS84toRD(wtr_stns.lat.values, wtr_stns.lon.values)
        wtr_stns.insert(loc=1, column='xrd', value=np.round(x,0))
        wtr_stns.insert(loc=2, column='yrd', value=np.round(y,0))

        return wtr_stns.sort_values(by='stn_name')

    @property
    def duplicate_station_codes(self):
        """Return names of KNMI weather stations and KNMI precipitation 
        stations with the same code."""

        wtrstn = self.get_weather_stations(geo=False)
        wtrstn = wtrstn[['stn_name']].squeeze()

        prcstn = self.get_precipitation_stations(geo=False)
        prcstn = prcstn[['stn_name']].squeeze()

        common_stn = np.intersect1d(prcstn.index.values, wtrstn.index.values)
        common = pd.merge(prcstn[common_stn], wtrstn[common_stn], 
            left_index=True, right_index=True, how='inner', 
            suffixes=('_prec','_wtr'))

        return common

    @property
    def duplicate_station_names(self):
        """Return codes of KNMI weather stations and KNMI precipitation 
        stations with the same name."""

        wtrstn = self.get_weather_stations(geo=False)
        wtrstn = wtrstn[['stn_name']].reset_index().set_index('stn_name').squeeze()

        prcstn = self.get_precipitation_stations(geo=False)
        prcstn = prcstn[['stn_name']].reset_index().set_index('stn_name').squeeze()

        common_names = np.intersect1d(prcstn.index.values, wtrstn.index.values)
        common = pd.merge(prcstn[common_names], wtrstn.loc[common_names], 
            left_index=True, right_index=True, how='inner', 
            suffixes=('_prec','_wtr'))

        return common
