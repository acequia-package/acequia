
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
import geopandas as gpd

from .._core.gwseries import GwSeries


class Dawaco:
    """Manage DAWACO ground water heads data set.

    Constructor
    -----------
    from_excel
        Read DAWACO hydroseries xlsx export file and return Dawaco object.
       
    """
    COLUMNS_MAPPING = {
        'Meetpuntcode' : 'locname',
        'X-coor.(m)' : 'xcr',
        'Y-coor.(m)' : 'ycr',
        'Maaiveld' : 'surfacelevel',
        'Startdatum' : 'startdate',
        'Bkb (m NAP)':'mplevel',
        'Bk Filt' : 'filtop',
        'Ok Filt' : 'filbot',
        'Filter' : 'filname',
        'Datum_Tijd' : 'headdatetime',
        'Waarde (m -NAP)' : 'headnap',
        'Waarde (m -Rp)' : 'headmp',
        'Waarde (m -Mv)' : 'headsurf',
        'Betrouwbaarheid' : 'reliability',
        'Opmerking' : 'remarks',
        
        #'Maaiveld (m NAP)' : 'surface',
        #'Datum': 'date',
        #'Tijd': 'time',
        }

    def __init__(self, rawdata=None, fpath=None, title=None):

        self._rawdata = rawdata
        self.fpath = fpath
        self.title = title
        if title is None:
            self.title = 'DAWACO dataset'

        self.data = self._rawdata.copy()
        self.data = self.data.rename(columns=self.COLUMNS_MAPPING)
        self.data = self.data.sort_values(by=['locname','filname','headdatetime']).copy()

        # DAWACO codes missing data for measurements in mNAP as 
        # values -90, -91, -92, -96, etc.
        self.data.loc[self.data['headmp']>=90,'headmp'] = np.nan
        self.data.loc[self.data['headsurf']<=90,'headsurf'] = np.nan
        self.data.loc[self.data['headnap']<=-90,'headnap'] = np.nan


    def __repr__(self):
        #return f'{self.__class__.__name__} (n={len(self)})'
        return f'{self.title} (n={len(self)})'


    def __len__(self):
        seriescount = len(self.data[['locname','filname']].drop_duplicates())
        return seriescount


    @classmethod
    def from_excel(cls, fpath, title=None):
        """Import Dawaco dataset from Excel export format.

        Parameters
        ----------
        fpath : str
            Path to DAWACO csv export file.
        title : str, optional
            User defined title of dataset.

        Returns
        -------
        Dawaco
            Object with exported data.
                
        """
        rawdata = pd.read_excel(fpath)     

        # validate data columns
        rawdata['Datum_Tijd'] = pd.to_datetime(
            rawdata['Datum'].astype(str) + ' ' + rawdata['Tijd'].astype(str)
            )
        rawdata['Filter'] = rawdata['Filter'].astype(str)

        return cls(rawdata=rawdata, fpath=fpath, title=title)

    @classmethod
    def from_csv(cls, fpath, title=None, sep=';'):
        """Import Dawaco dataset from csv export format.
        
        Parameters
        ----------
        fpath : str
            Path to DAWACO csv export file.
        title : str, optional
            User defined title.
        sep : str, default ';'
            Separator used in csv file.

        Returns
        -------
        Dawaco
            Object with exported data.
                
        """
        rawdata = pd.read_csv(fpath, sep=sep, low_memory=False)

        # validate columns
        rawdata['Startdatum'] = pd.to_datetime(rawdata['Startdatum'], format= '%d-%m-%Y')
        rawdata['Datum_Tijd'] = pd.to_datetime(
            rawdata['Datum'] + ' ' + rawdata['Tijd'],
            format= '%d-%m-%Y %H:%M')
        rawdata['Filter'] = rawdata['Filter'].astype('str')

        # return DAWACO object
        return cls(rawdata=rawdata, fpath=fpath, title=title)


    @property
    def items(self):
        """Return list of tuples with (locname, filter) for all filters."""
        filters = self.data[['locname','filname']].drop_duplicates()
        return list(zip(filters['locname'],filters['filname']))


    def get_gwseries(self, loc, fil):
        """Return GwSeries instance."""

        if not loc in self.data['locname'].unique():
            raise(f'Invalid location name {loc}.')

        if not fil in self.data[self.data['locname']==loc]['filname'].unique():
            raise(f'Invalid filter name {fil}.')

        # select series from data
        mask_loc = self.data['locname']==loc
        mask_fil = self.data['filname']==fil
        data = self.data[mask_loc & mask_fil].copy()

        # locprops
        locprops = Series(index=GwSeries.LOCPROPS_NAMES, dtype='object')
        locprops['locname'] = loc
        locprops['filname'] = fil
        locprops['alias'] = np.nan
        locprops['xcr'] = data['xcr'].unique()[0]
        locprops['ycr'] = data['ycr'].unique()[0]
        locprops['height_datum'] = 'NAP'
        locprops['grid_reference'] = 'RD'

        # tubeprops
        tp = GwSeries._tubeprops = DataFrame(columns=GwSeries.TUBEPROPS_NAMES)

        colnames = ['startdate','mplevel','filtop','filbot','surfacelevel']
        df = data.drop_duplicates(subset=colnames, keep='first', 
            ignore_index=True)
        for col in GwSeries.TUBEPROPS_NAMES:
            if col in colnames:
                tp[col] = df[col]

        # heads
        obs = pd.DataFrame(columns=GwSeries.HEADPROPS_NAMES)
        colnames = ['headdatetime', 'headmp', 'remarks']
        df2 = data.drop_duplicates(subset=colnames, keep='first', 
            ignore_index=True)
        for col in GwSeries.HEADPROPS_NAMES:
            if col in colnames:
                obs[col] = df2[col]

        return GwSeries(heads=obs, locprops=locprops, tubeprops=tp)

    def iteritems(self):
        """Iterate over all groundwater head series and return gwseries objects."""

        for (loc,fil), tbl in self.data.groupby(['locname','filname']):
            gw = self.get_gwseries(loc,fil)
            yield gw

    @property
    def welltube_locations(self):
        """Locations of well tubes as GeoDataFrame."""
        records = []
        for (locname,filname), tbl in self.data.groupby(by=['locname','filname']):
            rec = {}
            rec['locname'] = locname
            rec['filname'] = filname
            rec['firstdate'] = tbl['headdatetime'].min().strftime('%d-%m-%Y')
            rec['lastdate'] = tbl['headdatetime'].max().strftime('%d-%m-%Y')
            for colname in ['surfacelevel','filtop','filbot','xcr','ycr']:
                rec[colname] = tbl[colname].unique()[0]
            records.append(rec.copy())
        df = DataFrame(records)
        df = df.rename(columns={'surfacelevel':'surface'})

        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df['xcr'], df['ycr']), crs="EPSG:28992")
        return gdf


