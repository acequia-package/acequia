
import re
import os
import warnings
import datetime as dt
import numpy as np
from pandas import Series,DataFrame
import pandas as pd
import geopandas as gpd
##from shapely.geometry import Point
from .._core.gwseries import GwSeries
from .._geo.waypoint_kml import WpKml


class WaterWeb:
    """
    Manage WaterWeb dataset

    Constructor
    -----------
    from_csv
        Read waterweb csv export file and return WaterWeb object.

    """
    SEP = ';'
    NAMECOL = 'sunseries' # 'sunseries'

    COLUMN_MAPPING = {
        'Locatie':'sunloc',
        'SUN-code':'sunseries',
        'SUNcode':'sunseries',
        'NITG-code':'nitgcode',
        'NITGcode':'nitgcode',
        'BROID':'broid',
        'DERDEN-code':'derdencode',
        'DERDENcode':'derdencode',
        'X coordinaat':'xcr',
        'Y coordinaat':'ycr',
        'NAP hoogte bovenkant peilbuis':'mpcmnap',
        'Hoogte maaiveld tov NAP':'mvcmnap',
        'Hoogte maaiveld tov Nulpunt':'mvcmmp',
        'NAP hoogte bovenkant filter':'filtopcmnap',
        'NAP hoogte onderkant filter':'filbotcmnap',
        'Peilmoment':'datetime',
        'Peilstand tov Nulpunt' : 'peilcmmp',
        'Peilstand tov Nulpunt in Meters':'peilmmp',
        'Peilstand tov NAP':'peilcmnap',
        'Peilstand tov NAP in Meters':'peilmnap',
        'Peilstand tov maaiveld':'peilcmmv',
        'Peilstand tov maaiveld in Meters':'peilmmv',
        'Peilcode':'peilcode',
        'Opmerking bij peiling':'peilopm',
        'Watertemperatuur (°C)':'watertemp', 
        'Luchttemperatuur (°C)':'luchttemp', 
        'Luchtdruk (hPa)':'luchtdruk_hpa', 
        'Totaaldruk (hPa)':'totaaldruk_hpa', 
        'Waterdruk (hPa)':'waterdruk_hpa', 
        'Geleidbaarheid (μS/cm)':'conductance_muscm',
        }

         #'OLGA-kode':'olga', # DEZE KOLOM IS VERVALLEN
         #'Hoogte maaiveld tov maaiveld':'mvmv',
         #'Peilstand':'peilcmmp',
         #'Peilstand in Meters':'peilmmp',
         #'Peilstand in tov Nulpunt Meters' : 'peilmmp',

    EXPECTED_COLUMNS = ['sunloc', 'sunseries', 'nitgcode', 'derdencode',
        'xcr', 'ycr', 'mpcmnap', 'mvcmnap', 'mvcmmp', 'filtopcmnap',
        'filbotcmnap', 'datetime', 'peilcmmp', 'peilmmp', 'peilcmnap',  
        'peilmmv', 'peilcmmv', 'peilmmv', 'watertemp', 'luchttemp', 
        'luchtdruk_hpa', 'totaaldruk_hpa', 'waterdruk_hpa', 
        'conductance_muscm', 'peilcode', 'peilopm',
        ]

    SERIESPROPS_COLS = ['sunseries','sunlabel','derdencode','nitgcode',
        'mptype','meetnet','xcr','ycr',]

    LOCPROPS_COLS = ['sunloc','sunseries','nitgcode','derdencode',
        'xcr','ycr',]

    TUBEPROPS_COLS = ['mpcmnap','mvcmnap','filtopcmnap','filbotcmnap']

    LEVELDATA_COLS = ['datetime','peilmmp','peilcode','peilopm']

    NUMERIC_COLS = ['xcr', 'ycr', 'mpcmnap', 'mvcmnap', 'mvcmmp', 
        'filtopcmnap', 'filbotcmnap', 'peilcmmp', 'peilmmp',
        'peilcmnap', 'peilmnap', 'peilcmmv', 'peilmmv',
        'watertemp', 'luchttemp', 'luchtdruk_hpa', 
        'totaaldruk_hpa', 'waterdruk_hpa', 'conductance_muscm',
        ]

    LOCPROPS_MAPPING = {
        'locname':'sunloc','alias':'nitgcode',
        'xcr':'xcr','ycr':'ycr'
        }

    TUBEPROPS_MAPPING = {
        'startdate':'datetime','mplevel':'mpcmnap',
        'filtop':'filtopcmnap','filbot':'filbotcmnap',
        'surfacelevel':'mvcmnap'
        }

    LEVELS_MAPPING = {
        'headdatetime':'datetime', 'headmp':'peilmmp',
        'headnote':'peilcode','remarks':'peilopm'}

    REFLEVELS = [
        'datum','surface','mp',
        ]

    MEASUREMENT_TYPES = ['B','S','L','P','M']
    
    CAPITALS = [chr(x) for x in range(65,91)]

    KMLSTYLES = {
        'B':
            {'iconshape':'circle', 'iconscale':1.2,
             'iconcolor':'#0000FF','lobalescale':0.7,
             'labelcolor':'FFFFFF'},                
        'S':
            {'iconshape':'circle', 'iconscale':1.2,
             'iconcolor':'#1ca3ec','lobalescale':0.7,
             'labelcolor':'FFFFFF'},                
        'L':
            {'iconshape':'circle', 'iconscale':1.2,
             'iconcolor':'#2389da','lobalescale':0.7,
             'labelcolor':'FFFFFF'},                
        'P':
            {'iconshape':'circle', 'iconscale':1.2,
             'iconcolor':'#5abcd8','lobalescale':0.7,
             'labelcolor':'FFFFFF'},                
        'M':
            {'iconshape':'circle', 'iconscale':1.2,
             'iconcolor':'#ccff00','lobalescale':0.7,
             'labelcolor':'FFFFFF'},                
        }

    def __init__(self, data=None, fpath=None, network=None, rawdata=None):
        """Parameters
        ----------
        data : pandas DataFrame
            Table with measurements.

        fpath : str
            Filepath to data file.

        network : str
            User defined network name.
        
        rawdata : pandas DataFrame
            Table with original data read from input file.

        Notes
        -----
        To create WaterWeb instance from a file exported from the 
        WaterWeb website, use the class constructor:
        >>> wwn = WaterWeb.from_csv(fpath, network=<user defined name>)
               
        """

        if data is None:
            data = DataFrame(columns=self.EXPECTED_COLUMNS)

        if not isinstance(data, pd.DataFrame):
            raise ValueError((f'{data} is not a valid Pandas '
                f'DataFrame.'))

        self.data = data
        #self._rawdata = rawdata
        self.fpath = fpath
        self.network = network


    def __repr__(self):
        return (f'{self.network} (n={self.__len__()})')


    def __len__(self):
        return len(self.names)


    @classmethod
    def from_csv(cls,fpath,network=None):
        """ 
        Read waterweb csv network file and return new WaterWeb object

        Parameters
        ----------
        filepath : str
            path to waterweb csv export file

        networkname : str, optional
            name of network

        Returns
        -------
        WaterWebNetwork object
           
        """

        # read csv file
        try:
            rawdata = pd.read_csv(fpath, sep=cls.SEP, decimal=',', low_memory=False)
            rawdata.columns = [col.strip() for col in rawdata.columns] # remove space before column names
        except FileNotFoundError as err:
            raise FileNotFoundError(f'Invalid filepath for WaterWeb csv file: "{fpath}"')

        if network is None:
            #network = pathlib.Path(fpath).stem
            network = os.path.splitext(os.path.basename(fpath))[0]

        # check for unknown columns
        unknown_columns = []
        for col in list(rawdata):
            if col not in cls.COLUMN_MAPPING.keys():
                unknown_columns.append(col)
        if unknown_columns:
            raise ValueError((f'Unknown columns in WaterWeb csv file: '
                f'{unknown_columns}.'))

        # rename columns
        data = rawdata.rename(columns=cls.COLUMN_MAPPING)

        #check for missing columns
        missing_columns = []
        for col in cls.EXPECTED_COLUMNS:
            if col not in list(data):
                missing_columns.append(col)
        if missing_columns:
            raise ValueError((f'Missing columns in WaterWeb csv file: '
                f'{" ".join(missing_columns)}'))

        # change data column contents
        data['datetime'] = pd.to_datetime(data['datetime'], format="%Y-%m-%d %H:%M:%S",)
        data['nitgcode'] = data['nitgcode'].apply(
            lambda x:x[:8]+"_"+x[-3:].lstrip('0') if not pd.isnull(x) else np.nan)
        for col in cls.NUMERIC_COLS:
            data[col] = pd.to_numeric(data[col], errors='coerce')

        return cls(data, fpath=fpath, network=network, rawdata=rawdata)


    def _clean_raw_data(self):
        """Return dataframe with clean data from rawdata table."""


        # remove datarows with incomplete data
        # Note:
        # In WaterWeb exports, when measurements with dates earlier than 
        # the given startdate date or after the given enddate of the 
        # series are present, WaterWeb csv exports contains no metadata.
        # As a result, the first column of data does not contain the 
        # SUN-code, but the date of the measurement.
        # All these rows are removed and a user warnimg is given.
        dates = pd.to_datetime(data['datetime'], errors='coerce')
        first_col_is_date = ~dates.isnull()
        if not data[first_col_is_date].empty:
            warnings.warn((f'{len(data[first_col_is_date])} '
                f'measurements taken before given startdate or'
                f'after given enddate were removed from '
                f'{self.networkname}'))
            data = data[~first_col_is_date].copy()



    @property
    def names(self):
        """Return list of series names"""
        if self.data is not None:
            return list(self.data[self.NAMECOL].unique())
        else:
            return []


    @property
    def locnames(self):
        """Return list of series names"""
        
        # series suncodes end with a capital ('A', 'B') when mulitple
        # filters are present. A filter from a single well with one filter
        # ends with nothing

        if not all([self.is_suncode(name) for name in self.names]):
            raise ValueError((f'{self.networkname} contains invalid series '
                'names: {self.names}.'))

        locs = [x if x[-1] not in self.CAPITALS else x[:-1] for x in self.names]
        return set(locs)


    def is_suncode(self, srname):
        """Return TRUE if given string is standard SUN series name."""

        # define SUNcode regex pattern
        networknr = '[0-9]{8}'
        mptypes = ''.join((self.MEASUREMENT_TYPES))
        locnr = '[0-9]{3}'
        tubecode = '[A-Z]'
        pattern = fr'^{networknr}[{mptypes}]{locnr}{tubecode}?$'
        # (Examples of valid SUN-code patterns are: 
        # '12345678B001', '12345678B001A')

        # search for pattern
        sunpat = re.compile(pattern)
        if sunpat.match(srname) is None:
            is_suncode = False
        else:
            is_suncode = True

        return is_suncode


    def get_measurement_type(self, srname=None):
        """Return kind of measurement type series

        Parameters
        ----------
        srname : str, optional
            series name, if not given, type of all series is returned

        Returns
        -------
        str, numpy array of str """

        srnames = self.names
        sr = Series(data=srnames, index=srnames, name='seriestype')
        sr = sr.apply(lambda x:x[8])

        if srname is not None:
            sr = sr[srname]

        return sr


    @property
    def measurement_types(self):
        """Return table of measurement type counts."""
        srtypelist = []
        for name in self.names:
            srtypelist.append(self.get_measurement_type(name))
        tbl = pd.Series(srtypelist).value_counts()
        tbl.name = self.networkname
        return tbl


    def get_locname(self, srname):
        """Return location name for given series

        Parameters
        ----------
        srname : str
            name of series to return """

        return self.get_locprops(srname)['sunloc']


    def get_filname(self, srname, style='sun'):
        """Return filter name for given series

        Parameters
        ----------
        srname : str
            Name of series to return.
        style : {'sun', 'dino'}, default 'sun'
            Use SUN naming style (letters) or DINO style (numbers).

        Notes
        -----
        In WaterWeb, well filters are named using capitals (A, B, etc), 
        with the most shallow filter starting as "A". When only one filter 
        is present, no lettercode is added, so location code and filter 
        code are equal. This style originates from the former SUN-database, 
        used until 2019 by nature management organisations in the 
        Netherlands.
        DINO-style uses numbers for well piezometers (1, 2, etc), with 
        the most shallow filter starting as 1. This convention was used in
        the national groundwater database managend by TNO.
           
        """
        if style not in ['sun','dino']:
            raise ValueError((f'Naming style should be "sun" or "dino", '
                f'not {style}.'))

        # get sunstyle filter name
        srname = self.get_locprops(srname)['sunseries']
        capitals = [chr(i) for i in range(65,91)]
        if srname[-1] in capitals:
            filname = srname[-1]
        else:
            filname = ''

        # convert to dino-style
        if style=='dino':
            if filname in capitals:
                filname = capitals.index(filname) + 1
            elif filname=='':
                filname = 1
            else:
                raise ValueError((f'Sun filter name should be a capital '
                    f'or empty, but not "{filname}" (ValueError in series'
                    f'{srname}'))

        return filname


    @property
    def networkname(self):
        """Return network name

        Parameters
        ----------
        name : str, optional
            name of measurement network """
        if self.network is None:
            name = '<onbekend meetnet>'
        else:
            name = self.network
        return name


    @networkname.setter
    def networkname(self,name):
        self.network = name


    def get_locprops(self, srname):
        """Return series location properties

        Parameters
        ----------
        sunseries : str
            name of series to return

        Return
        ------
        pd.Series """

        data = self.data[self.data[self.NAMECOL]==srname]
        lastrow = data.iloc[-1,:]

        sr = Series(
            index = self.LOCPROPS_COLS,
            dtype = 'object',
            name = srname)

        for col in self.LOCPROPS_COLS:
            sr[col] = lastrow[col]

        return sr


    def get_tubeprops(self,srname):
        """Return welltube properties

        Parameters
        ----------
        sunseries : str
            name of series

        Returns
        -------
        pd.DataFrame """

        data = self.data[self.data[self.NAMECOL]==srname]
        data = data.drop_duplicates(
            subset=self.TUBEPROPS_COLS,
            keep='first')

        colnames = ['datetime'] + self.TUBEPROPS_COLS
        data = data[colnames].reset_index(drop=True)
        return data

    def get_levels(self, srname, ref='datum'):
        """Return measured water levels in unit meter.

        Parameters
        ----------
        srname : str
            Name of series.
        ref : {'mp','datum',' surface'}, default 'datum' 
            Reference point for measured levels.

        Returns
        -------
        pd.Series """

        if ref not in self.REFLEVELS:
            warnings.warn((f'{ref} not in {self._references}. '),
                (f'reference is set to "datum".')) 
            ref = 'datum'

        if ref=='mp':
            col = 'peilmmp'
        if ref=='datum':
            col = 'peilmnap'
        if ref=='surface':
            col = 'peilmmv'

        data = self.data[self.data[self.NAMECOL]==srname]
        data = data[[col,'datetime']]
        
        sr = data.set_index('datetime',drop=True).squeeze()
        sr.name = self.get_locname(srname)
        sr.index.name = 'datetime' 
 
        return sr[sr.notnull()]

    def get_leveldata(self, srname, ref='datum'):
        """Return measured levels including remarks.

        Parameters
        ----------
        srname : str
            Name of series.
        ref : {'mp','datum',' surface'}, default 'datum' 
            Reference point for measured levels.

        Returns
        -------
        pd.Series """
   
        levels =self.data[self.data[self.NAMECOL]==srname]
        levels = levels[self.LEVELDATA_COLS]
        return levels

    def get_gwseries(self,srname):
        """Return gwseries obect for one series

        Parameters
        ----------
        srname : str
            name of series to return

        Returns
        -------
        acequia.GwSeries

        """

        gw = GwSeries()

        # locprops
        locprops = self.get_locprops(srname)
        for gwprop in list(gw._locprops.index):
            if gwprop not in self.LOCPROPS_MAPPING.keys():
                continue
            wwnprop = self.LOCPROPS_MAPPING[gwprop]
            gw._locprops[gwprop] = locprops[wwnprop]

        gw._locprops['filname'] = self.get_filname(srname, style='dino')
        gw._locprops['height_datum'] = 'mNAP'
        gw._locprops['grid_reference'] = 'RD'

        # tubeprops
        tubeprops = self.get_tubeprops(srname)
        for gwprop in list(gw._tubeprops):
            if gwprop not in self.TUBEPROPS_MAPPING.keys():
                continue
            wwnprop = self.TUBEPROPS_MAPPING[gwprop]
            gw._tubeprops[gwprop] = tubeprops[wwnprop].values

            if gwprop in gw.TUBEPROPS_NUMCOLS:
                # waterweb uses cm, gwseries expects meter
                gw._tubeprops[gwprop] = gw._tubeprops[gwprop].astype('float')/100.

        #levels
        levels = self.get_leveldata(srname, ref='datum')
        for gwprop in list(gw.HEADPROPS_NAMES):
            if gwprop not in self.LEVELS_MAPPING.keys():
                continue
            wwnprop = self.LEVELS_MAPPING[gwprop]
            gw._obs[gwprop] = levels[wwnprop].values
        #gw._obs['headmp'] = gw._obs['headmp']/100.

        return gw

    def get_series_shortname(self, srname, as_location=False):
        """Return short version of suncode.

         Parameters
        ----------
        srname : str
            SUNcode of series.
        as_location : bool, default False
            Keep (False) or remove filter code (True).

        Returns
        -------
        str
            
        """
        if not self.is_suncode(srname):
            raise ValueError((f'{srname} is not a valid suncode.'))

        mptype = self.get_measurement_type(srname)
        srnumber = srname[9:12].lstrip('0')
        fil = self.get_filname(srname, style='sun')

        if not as_location:
            shortname = f'{mptype}{srnumber}{fil}'
        else:
            shortname = f'{mptype}{srnumber}'

        return shortname


    @property
    def series_properties(self):
        """Return metadata for all measurement series."""

        # series properties to dataframe
        properties = []
        for srname in self.names:
            sr = self.get_locprops(srname)
            sr['mptype'] = self.get_measurement_type(srname)
            sr['meetnet'] = self.networkname

            gw = self.get_gwseries(srname)
            sr['lastdate'] = gw.heads().index.max().strftime('%Y-%m-%d')

            properties.append(DataFrame(sr).T)

        df = pd.concat(properties,ignore_index=True)

        # add columns serieslabel
        shortnames = [self.get_series_shortname(srname, as_location=False)
            for srname in self.names]
        df['sunlabel'] = shortnames

        # order columns
        #colnames = ['sunseries','sunlabel','broid','derdencode','nitgcode',
        #    'mptype','meetnet','xcr','ycr',]
        
        cols = self.SERIESPROPS_COLS
        df = df[cols + [c for c in df.columns if c not in cols]]

        # create geodataframe
        gdf = gpd.GeoDataFrame(df, 
            geometry=gpd.points_from_xy(
                df['xcr'], df['ycr'], 
            crs='EPSG:28992'))        

        return gdf


    @property
    def location_properties(self):
        """Return locations as GeoDataFrame."""

        # get series properties as pandas dataframe
        srprops = self.series_properties

        # insert sunlocations column
        sunseries = srprops['sunseries'].to_list()
        sunlocs = [self.get_locname(srname) for srname in sunseries]
        srprops.insert(0, 'sunloc', sunlocs)

        # merge series to locations
        locprops = srprops.drop_duplicates(subset=['sunloc'], keep='first')

        # recalculate sun shortname
        shortnames = [self.get_series_shortname(srname, as_location=True)
            for srname in locprops['sunseries'].to_list()]
        locprops['sunlabel'] = shortnames

        # remove filter names from nitgcode
        locprops['nitgcode'] = locprops['nitgcode'].str.split('_').str[0]

        # drop series name columns
        locprops = locprops.drop(columns='sunseries')

        return locprops


    def to_kml(self,filepath):
        """Save locations to KML file.
        
        Parameters
        ----------
        filepath : str
            Valid path to output file.

        Returns
        -------
        wp : WpKml
        """

        locs = self.location_properties
        colnames = [col for col in list(locs) if col not in ['geometry']]
        wp = WpKml(locs[colnames],label='label',xcoor='xcr',ycoor='ycr',
            styledict=self.KMLSTYLES,stylecol='mptype')
        wp.writekml(filepath)
        return wp


    def to_gpx(self,filepath):
        """Save locations to GPX waypoints file.
        
        Parameters
        ----------
        filepath :str
            Valid filepath for saving GPX file.

        Returns
        -------
        GeoDataFrame
            GPX data that have been saved.
        """
        # source for this solution:
        # https://github.com/geopandas/geopandas/issues/684
        # jose1911 suggestes adding all requeierd files to dataframe en 

        locs = self.locations.copy()
        locs = locs.to_crs(4326)

        # adding columns that are probably expected by apps that import
        # gpx waypoint files.
        locs['name']=locs['label']
        locs['ele']=0.0
        locs['magvar']=0.0
        locs['time'] = dt.datetime.now() #'2019-08-02T14:17:50Z'
        locs['geoidheight'] = 0.0
        colnames = ['geometry', 'ele', 'time', 'magvar', 'geoidheight', 'name']
        
        # saving gpx file
        if not filepath.endswith('.gpx'):
            filepath = f'{filepath}.gpx'
        locs[colnames].to_file(filepath,'GPX')
        return locs[colnames]


    def to_shapefile(self, filepath):
    
        locs = self.locations
        locs['xcr'] = locs['xcr'].astype('float')
        locs['ycr'] = locs['ycr'].astype('float')
        locs.to_file(f'{filepath}.shp')
        return locs


    def iteritems(self):
        """Iterate over all series and return gwseries object."""
        for srname in self.names:
            yield self.get_gwseries(srname)

