
import pathlib
import warnings
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
    NAMECOL = 'sunsr'

    COLUMN_MAPPING = {
        'Lokatie':'sunloc',
        'SUN-kode':'sunsr',
        'NITG-kode':'nitgsr',
         #'OLGA-kode':'olga', # DEZE KOLOM IS VERVALLEN
        'BROID':'broid',
        'DERDEN-kode':'derden',
        'X coordinaat':'xcr',
        'Y coordinaat':'ycr',
        'NAP hoogte bovenkant peilbuis':'mpnap',
        'Hoogte maaiveld tov NAP':'mvnap',
        'Hoogte maaiveld tov Nulpunt':'mvmp',
        'Hoogte maaiveld tov maaiveld':'mvmv',
        'NAP hoogte bovenkant filter':'filtopnap',
        'NAP hoogte onderkant filter':'filbotnap',
        'Peilmoment':'datetime',
        'Peilstand':'peilcmmp',
        'Peilstand in Meters':'peilmmp',
        'Peilstand tov NAP':'peilcmnap',
        'Peilstand tov NAP in Meters':'peilmnap',
        'Peilstand tov maaiveld':'peilcmmv',
        'Peilstand tov maaiveld in Meters':'peilmmv',
        'Peilkode':'peilcode',
        'Opmerking bij peiling':'peilopm'
        }

    LOCPROPS_COLS = ['sunloc','sunsr','nitgsr','broid','derden',
        'xcr','ycr',]

    TUBEPROPS_COLS = ['mpnap','mvnap','filtopnap','filbotnap']

    PEILPROPS_COLS = ['datetime','peilcmmp','peilcode','peilopm']

    LOCPROPS_MAPPING = {
        'locname':'sunloc','alias':'nitgsr',
        'xcr':'xcr','ycr':'ycr'
        }

    TUBEPROPS_MAPPING = {
        'startdate':'datetime','mplevel':'mpnap',
        'filtop':'filtopnap','filbot':'filbotnap',
        'surfacelevel':'mvnap'
        }

    LEVELS_MAPPING = {
        'headdatetime':'datetime', 'headmp':'peilcmmp', 
        'headnote':'peilcode','remarks':'peilopm'}

    REFLEVELS = [
        'datum','surface','mp',
        ]

    MEASUREMENT_TYPES = ['B','S','L','P']

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
        }


    def __init__(self,fpath=None,data=None,network=None):

        self._fpath = fpath
        self._network = network
        self._rawdata = data
        self.data = data

        if self._network is None:
            self._network = '<unknown network>'

        if self.data is not None:

            if not isinstance(self.data,pd.DataFrame):
                raise ValueError((f'{self.data} is not a valid Pandas '
                    f'DataFrame.'))

            # rename columns in data
            self.data = self.data.rename(columns=self.COLUMN_MAPPING)

            # Remove measurements without reference level.
            # Note:
            # When thera are measurements with dates earlier than the
            # first date with technical tube data, the waterweb csv 
            # export starts with measurments without technical data.
            # These are removed and a user warnimg is given.
            hasnoref = self.data['mpnap'].isnull()
            if len(self.data[hasnoref])!=0:
                warnings.warn((f'{len(self.data[hasnoref])} measurements '
                    f'were removed from {self.networkname}'))
                self.data = self.data[~hasnoref].copy()

    def __repr__(self):
        return (f'{self._network} (n={self.__len__()})')


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
        ...
        """
        try:
            data = pd.read_csv(fpath,sep=';',decimal=',')
        except FileNotFoundError as err:
            raise FileNotFoundError(f'Invalid filepath for WaterWeb csv file: "{fpath}"')

        if network is None:
            network = pathlib.Path(fpath).stem

        #check for missing columns
        missing_columns = []
        for col in cls.COLUMN_MAPPING.keys():
            if col not in list(data):
                missing_columns.append(col)
        if missing_columns:
            warnings.warn((f'Missing columns in WaterWeb csv file: '
                f'{missing_columns}'))

        # check for unknown columns
        unknown_columns = []
        for col in list(data):
            if col not in cls.COLUMN_MAPPING.keys():
                unknown_columns.append(col)
        if unknown_columns:
            warnings.warn((f'Unknown columns in WaterWeb csv file: '
                f'{unknown_columns}.'))

        ## change column types
        ##data = data.astype(dtype=cls._typedict)

        # change column contents
        data['Peilmoment'] = pd.to_datetime(data['Peilmoment'])
        data['NITG-kode'] = data['NITG-kode'].apply(
            lambda x:x[:8]+"_"+x[-3:].lstrip('0') if not pd.isnull(x) else np.nan)

        return cls(fpath=fpath,data=data,network=network)


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
        # filters are present. A filter from a well with one filter
        # ends with nothing
        capitals = [chr(x) for x in range(65,91)]
        locs = [x if x[-1] not in capitals else x[:-1] for x in self.names]
        return set(locs)


    def get_type(self,srname=None):
        """Return kind of measurement type series

        Parameters
        ----------
        srname : str, optional
            series name, if not given, type of all series is returned

        Returns
        -------
        str, numpy array of str """

        srnames = self.names
        sr = Series(data=srnames,index=srnames,name='seriestype')
        sr = sr.apply(lambda x:x[8])

        if srname is not None:
            return sr[srname]

        return sr

    @property
    def measurement_types(self):
        """Return table of measurement type counts."""
        srtypelist = []
        for name in self.names:
            srtypelist.append(self.get_type(name))
        tbl = pd.Series(srtypelist).value_counts()
        tbl.name = self.networkname
        return tbl


    def get_locname(self,srname):
        """Return location name for given series

        Parameters
        ----------
        srname : str
            name of series to return """

        return self.get_locprops(srname)['sunloc']


    def get_filname(self,srname):
        """Return filter name for given series

        Parameters
        ----------
        srname : str
            name of series to return 

        Notes
        -----
        WaterWeb uses the DINO-SUN convention of only explicitly naming
        filters if more than one filter is present."""

        filname = self.get_locprops(srname)['sunsr']
        if filname[-1].isalpha():
            return filname[-1]
        return ''


    @property
    def networkname(self):
        """Return network name

        Parameters
        ----------
        name : str, optional
            name of measurement network """
        return self._network

    @networkname.setter
    def networkname(self,name):
        self._network = name

    def get_locprops(self,srname):
        """Return series location properties

        Parameters
        ----------
        sunsr : str
            name of series to return

        Return
        ------
        pd.Series """

        data =self.data[self.data[self.NAMECOL]==srname]
        lastrow = data.iloc[-1,:]

        sr = Series(index=self.LOCPROPS_COLS,dtype='object',
            name=srname)
        for col in self.LOCPROPS_COLS:
            sr[col] = lastrow[col]

        return sr


    def get_tubeprops(self,srname):
        """Return welltube properties

        Parameters
        ----------
        sunsr : str
            name of series

        Returns
        -------
        pd.DataFrame """

        data =self.data[self.data[self.NAMECOL]==srname]
        data = data.drop_duplicates(subset=self.TUBEPROPS_COLS,
            keep='first')
        data = data[['datetime']+self.TUBEPROPS_COLS]
        data = data.reset_index(drop=True)

        return data

    def get_levels(self,srname,ref='mp'):
        """Return measured levels

        Parameters
        ----------
        srname : str
            name of series
        ref : {'mp','datum',' surface'}, default 'mp' 

        Returns
        -------
        pd.Series """

        if ref not in self.REFLEVELS:
            warnings.warn((f'{ref} not in {self._references}. '),
                (f'reference is set to "datum".')) 
            ref = 'datum'
        if ref=='mp':
            col = 'peilcmmp'
        if ref=='datum':
            col = 'peilmnap'
        if ref=='mv':
            col = 'peilcmmv'

        data =self.data[self.data[self.NAMECOL]==srname]
        data = data[[col,'datetime']]
        data = data.set_index('datetime',drop=True).squeeze()
        data.name = self.get_locname(srname)
        data.index.name = 'datetime' 
        data = data/100.

        return data


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

        gw._locprops['filname'] = self.get_filname(srname)
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
                gw._tubeprops[gwprop] = gw._tubeprops[gwprop]/100.

        #levels
        levels =self.data[self.data[self.NAMECOL]==srname]
        levels = levels[self.PEILPROPS_COLS]
        for gwprop in list(gw.HEADPROPS_NAMES):
            if gwprop not in self.LEVELS_MAPPING.keys():
                continue
            wwnprop = self.LEVELS_MAPPING[gwprop]
            gw._heads[gwprop] = levels[wwnprop].values
        gw._heads['headmp'] = gw._heads['headmp']/100.

        return gw

    @property
    def locations(self):
        """Return locations as GeoDataFrame."""

        propslist = []
        for srname in self.names:
            sr = self.get_locprops(srname)
            sr['name'] = sr.name
            sr['mptype'] = self.get_type(srname)
            sr['network'] = self.networkname
            propslist.append(DataFrame(sr).T)
        locprops = pd.concat(propslist,ignore_index=True)

        # from series to locations
        locprops = locprops.drop_duplicates(subset=['sunloc'], keep='first')
        nitg = locprops['nitgsr'].apply(lambda x:x.split('_')[0] if 
            not pd.isnull(x) else np.nan)
        locprops.insert(2,'nitgcode',nitg)
        locprops = locprops.drop(columns=['sunsr','nitgsr','name'])

        # add waypoint label column
        labels = locprops['sunloc'].str[8]+locprops['sunloc'].str[9:].str.lstrip('0')
        locprops.insert(0,'label',labels)

        gdf = gpd.GeoDataFrame(
            locprops, geometry=gpd.points_from_xy(
            locprops['xcr'], locprops['ycr'], crs='EPSG:28992'))

        return gdf

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

        locs = self.locations
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

        # adding columns that are propably expected by apps that import
        # gpx waypoint files.
        locs['name']=locs['label']
        locs['ele']=0
        locs['magvar']=0
        locs['time']='2019-08-02T14:17:50Z'
        locs['geoidheight'] = 0
        colnames = ['geometry', 'ele', 'time', 'magvar', 'geoidheight', 'name']
        
        # saving gpx file
        if not filepath.endswith('.gpx'):
            filepath = f'{filepath}.gpx'
        locs[colnames].to_file(filepath,'GPX')
        return locs[colnames]

    def iteritems(self):
        """Iterate over all series and return gwseries object."""
        for srname in self.names:
            yield self.get_gwseries(srname)