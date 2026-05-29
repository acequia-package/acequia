
import os
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
        # values must correspond with GwSeries object columns
        'Meetpuntcode' : 'locname',
        'Filter' : 'filname',
        'Status meetpunt':'statusmp',
        'Aantal filters':'filcount',
        'X-coor.(m)' : 'xcr',
        'Y-coor.(m)' : 'ycr',
        'Maaiveld' : 'surfacelevel',
        'Maaiveld (m NAP)' : 'surfacelevel',
        'Bkb (m NAP)':'mplevel',
        'BkB (m NAP)':'mplevel',
        'BkF (m NAP)':'filtop',
        'OkF (m+NAP)':'filbot',
        'Bk Filt' : 'filtop',
        'Ok Filt' : 'filbot',
        'Zandvang (m)':'sedslump',
        'Diameter (mm)':'tubediam',
        'Startdatum' : 'startdate',
        'Einddatum':'lastdate',
        'Vervaldatum':'expiredate',
        'Datum': 'headdate',
        'Tijd': 'headtime',
        'Datum_Tijd' : 'headdatetime',
        'Waarde (m -NAP)' : 'headnap',
        'Waarde (m NAP)' : 'headnap',
        'Waarde (m -Rp)' : 'headmp',
        'Waarde (m -Mv)' : 'headsurf',
        'Betrouwbaarheid' : 'reliability',
        'Opmerking' : 'remark', # Opmerking is for well properties
        'Opmerkingen':'remarks', # Opmerking is for head remarks
        'Type dm':'dmtype',
        'ID dm':'dmid',
        #
        'Locatie':'locatie', 
        'Gebiedsnaam':'gebiedsnaam', 
        'NITG-code':'nitgcode', 
        'BRO Rapportage':'brorapportage', 
        'BRO Id':'broid', 
        'BRO KvK-Bronhouder':'bronhouderid', 
        'BRO KvK-Eigenaar':'eigenaarid', 
        'BRO KvK-Ond.instantie':'beheerderid', 
        'BRO Kader':'brokader', 
        'BRO Kwaliteitsnorm':'brokwaliteit', 
        'BRO Initiële functie':'brofunctie', 
        'BRO Bepalingsmethode coördinaten':'methode_coordinaten', 
        'BRO Bepalingsmethode maaiveld':'methode_maaiveld', 
        'BRO Stabiel Mv':'maaiveld_stabiel', 
        'BRO Stabiel Mp':'mp_stabiel', 
        'BRO Putcode':'broputcode', 
        'RIVM_CODE':'rivmcode', 
        'BRO-info (waarde)':'broinfo', 
        'Type buis':'buistype', 
        'Aanvulmateriaal':'aanvulmateriaal', 
        'Materiaal buis':'materiaalbuis', 
        'Gebruikte lijm':'lijmgebruikt', 
        'Kous materiaal':'kousmateriaal', 
        'Uitgerust met drukdop':'drukdop', 
        'Variabele diameter':'diameter_veriabel', 
        'Status':'status', 
        'GLD-Id':'gldid',
        }

    COLUMNS_DATE = ['startdate','lastdate','expiredate',]
    COLUMNS_FLOAT = ['surfacelevel','mplevel','filtop','filbot','sedslump','tubediam','headnap','headmp','headsurf']

    GWSERIES_COLUMNS_MAPPING = {
        'locname':'locname',
        'filname':'filname',
        'xcr':'xcr',
        'ycr':'ycr',
        'headdatetime':'headdatetime',
        'headmp':'headmp',
        'remarks':'remarks',
        'startdate':'startdate',
        'mplevel':'mplevel',
        'filtop':'filtop',
        'filbot':'filbot',
        'surfacelevel':'surfacelevel'
        }

    def __init__(self, data=None, srcpath=None, title=None):
        """
        data : dataframe
            Groundwater measurements.
        
        srcpath : str
            Filepath to source.

        title : str
            User defined dataset name.

        Notes
        -----
        To read Dawaco dataset from file use the .from_csv or .from_excel
        methods.
                """

        self._rawdata = data
        self._srcpath = srcpath
        self._title = title
        
        if self._title is None:
            if os.path.isfile(self._srcpath):
                self._title = os.path.basename(self._srcpath).split(".")[0]
            if os.path.isdir(self._srcpath):
                self._title = os.path.basename(
                    os.path.dirname(self._srcpath))

        # validate data values
        self._data = self._rawdata.copy()

        # get missing columns from existing columns
        has_date = 'headdate' in self._data.columns
        has_time = 'headtime' in self._data.columns
        has_datetime = 'headdatetime' in self._data.columns
        if not has_datetime:
            if (has_date) & (has_time):
                self._data['headdatetime'] = self._data['headdate'] + ' ' + self._data['headtime']
            if (has_date) & (not has_time):
                self._data['headdatetime'] = self._data['headdate'] + ' 12:00'
        self._data['headdatetime'] = pd.to_datetime(self._data['headdatetime'], format= '%d-%m-%Y %H:%M')

        for col in self.COLUMNS_DATE:
            if col in self._data.columns:
                self._data[col] = pd.to_datetime(self._data[col], format= '%d-%m-%Y')

        for col in self.COLUMNS_FLOAT:
            if col in self._data.columns:
                self._data[col] = self._data[col].str.replace(",",".").astype('float')

        if 'headmp' not in self._data.columns:
            self._data['headmp'] = self._data['mplevel']-self._data['headnap']
        if 'headsurf' not in self._data.columns:
            self._data['headsurf'] = self._data['surfacelevel']-self._data['headnap']


        # DAWACO codes missing data for measurements in mNAP as 
        # values -90, -91, -92, -96, etc.
        """
        self._data.loc[self._data['headmp']>=90,'headmp'] = np.nan
        self._data.loc[self._data['headsurf']<=90,'headsurf'] = np.nan
        self._data.loc[self._data['headnap']<=-90,'headnap'] = np.nan
        """


    def __repr__(self):
        return f'{self._title} (n={len(self)})'


    def __len__(self):
        seriescount = len(self._data[['locname','filname']].drop_duplicates())
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
        rawdata = rawdata.rename(columns=self.COLUMNS_MAPPING)

        return cls(data=rawdata, srcpath=fpath, title=title)

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
        data = pd.read_csv(fpath, sep=sep, low_memory=False, dtype='object', encoding='latin-1')
        data = cls._validate_csv(data)
        return cls(data=data, srcpath=fpath, title=title)


    @classmethod
    def _validate_csv(cls, data):
        """Return validated data from raw Dawaco csv file."""

        # drop (traiing) columns with no name
        unnamed = [col for col in data.columns if col.startswith('Unnamed')]
        if unnamed:
            print(f"Dropped {len(unnamed)} columns with no name: {unnamed}.")
            data = data.drop(columns=unnamed)

        # check for unexpected columns
        expected = Dawaco.COLUMNS_MAPPING.keys()
        unexpected = [col for col in data.columns if col not in expected]
        if unexpected:
            raise ValueError(f"Found {len(unexpected)} unexpected columns names: {unexpected}.")

        # rename columns
        data = data.rename(columns=cls.COLUMNS_MAPPING)

        # check for presence of heads
        if 'headnap' not in data.columns:
            raise ValueError((f"Column with heads not available in source {fpath}. "
                f"Available columns names are: {list(data.columns)}."))

        return data


    @classmethod
    def from_csvfolder(cls, folder, title=None, sep=';'):
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
        ##fdir = r"..\src\peilbuisdata2\gwsnap_en_putgegevens\\"
        csvfiles = [fname for fname in os.listdir(folder) 
            if fname.endswith(".csv")]
        datalist = []
        sep=";"
        for file in csvfiles:
            fpath = os.path.join(folder, file)
            single = pd.read_csv(fpath, sep=sep, low_memory=False, 
                dtype='object')
            datalist.append(single.copy())
        data = pd.concat(datalist, ignore_index=True)

        data = cls._validate_csv(data)
        return cls(data=data, srcpath=folder, title=title)


    def items(self):
        """Return list of tuples with (locname, filter) for all tubes."""
        filters = self._data[['locname','filname']].drop_duplicates()
        return list(zip(filters['locname'],filters['filname']))


    def gwseries(self, loc, fil):
        """Return GwSeries instance.
        
        Parameters
        ----------
        loc : str
            Location name.
        fil : str|int
            Filter name.

        Returns
        -------
        GwSeries
        
        Notes
        -----
        For a list of location and filters names call the items method.
            
        """
        if not loc in self._data['locname'].unique():
            raise ValueError(f'Invalid location name {loc}.')

        if not str(fil) in (self._data[self._data['locname']==
            loc]['filname']).unique():
            raise ValueError(f"Invalid filter name '{fil}'.")

        # select series from data
        mask_loc = self._data['locname']==loc
        mask_fil = self._data['filname']==str(fil)
        data = self._data[mask_loc & mask_fil].copy()

        # GwSeries defaults
        gw = GwSeries()
        lp = gw._locprops
        tp = gw._tubeprops
        obs = gw._obs

        # locprops
        lp['locname'] = loc
        lp['filname'] = str(fil)
        lp['xcr'] = self._data['xcr'].unique()[0]
        lp['ycr'] = self._data['ycr'].unique()[0]

        # tubeprops
        colnames = ['startdate','mplevel','filtop','filbot','surfacelevel']
        tubeprops = data.drop_duplicates(subset=colnames, keep='first', 
            ignore_index=True)
        tp = DataFrame(columns=GwSeries.TUBEPROPS_NAMES)
        for col in tp.columns:
            if col in colnames:
                tp[col] = tubeprops[self.GWSERIES_COLUMNS_MAPPING[col]]

        # heads
        obs = pd.DataFrame(columns=GwSeries.HEADPROPS_NAMES)
        dawaco_columns = ['headdatetime', 'headmp', 'remarks']
        data_unique = data.drop_duplicates(
            subset=dawaco_columns, keep='first', 
            ignore_index=True)
        for col in GwSeries.HEADPROPS_NAMES:
            if col in dawaco_columns:
                obs[col] = data_unique[self.GWSERIES_COLUMNS_MAPPING[col]]

        return GwSeries(heads=obs, locprops=lp, tubeprops=tp)


    def iteritems(self):
        """Iterate over all groundwater head series and return gwseries 
        objects."""

        for (loc,fil), tbl in self._data.groupby(['locname','filname']):
            gw = self.gwseries(loc, fil)
            yield gw


    def tubes(self):
        """Locations of well tubes as GeoDataFrame."""
        records = []
        for (locname,filname), tbl in self._data.groupby(by=['locname',
            'filname']):
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
            df, geometry=gpd.points_from_xy(df['xcr'], df['ycr']), 
                crs="EPSG:28992")
        return gdf

    def wells(self):
        """Return well locations as GeoDataFrame."""
        aggdict={'filname':'count','firstdate':'min','lastdate':'max',
            'filtop':'max','filbot':'min', 'xcr':'first', 'ycr':'first'}
        locs = self.tubes().groupby('locname').agg(aggdict)
        locs = locs.rename(columns={'filname':'filcount'})

        geom = gpd.points_from_xy(locs['xcr'], locs['ycr'])
        locs = gpd.GeoDataFrame(
            locs, geometry=geom, crs="EPSG:28992")

        return locs