

import numpy as _np
import pandas as _pd
import geopandas as _gpd
import brodata as _brodata

from .._core.gwseries import GwSeries

class BroDataDinoGwl:
    """Download dino groundwater level data from dinoloket."""

    MAPPING_LOCPROPS = {
        'locname':'Locatie',
        'filname':'Filternummer',
        'alias':'Externe aanduiding',
        'alias2':_np.nan,
        'owner':_np.nan,
        'observer':_np.nan,
        'constructiondate':_np.nan,
        'surfacestable':_np.nan,
        'xcr':'X-coordinaat',
        'ycr':'Y-coordinaat',
        'height_datum':_np.nan, #'NAP',
        'grid_reference':_np.nan, #'EPSG:28992',
        }

    MAPPING_TUBEPROPS = {
        'startdate':'Startdatum', 
        'mplevel':'Meetpunt (cm t.o.v. NAP)',
        'filtop':'Bovenkant filter (cm t.o.v. NAP)',
        'filbot':'Onderkant filter (cm t.o.v. NAP)', 
        'surfacedate':'Datum maaiveld gemeten', 
        'surfacelevel':'Maaiveld (cm t.o.v. NAP)',
        }

    MAPPING_HEADPROPS = {
        'headdatetime':'Peildatum',
        'headmp':'Stand (cm t.o.v. MP)',
        'headnote':'Bijzonderheid',
        'remarks':'Opmerking',
        }

    def __init__(self, obs=None, wellprops=None, request=None):

        self._obs = obs
        self._wellprops = wellprops
        self._request = request

        self._check_expected_columns()


    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'
        
    def __len__(self):
        return len(self._obs)

    @classmethod
    def from_nitgcode(cls, nitgcode, tube):
        """Download groundwater level data for one tube.
        
        Parameters
        ----------
        nitgcode : str
            Nitgcode for well location.

        tube : int
            Tube number.

        Returns
        -------
        BroDataDinoGws
            
        """
        dinogw = _brodata.dino.Grondwaterstand.from_dino_nr(nitgcode, tube)
        
        wellprops = dinogw.meta
        for column in ['Datum maaiveld gemeten','Startdatum','Einddatum']:
            wellprops[column] = _pd.to_datetime(wellprops[column], dayfirst=True)

        return cls(obs=dinogw.data, wellprops=wellprops, request=_pd.Series(dinogw.props))


    def gwseries(self):
        """Return gwseries with dinogws data."""

        locprops = _pd.Series(index=GwSeries.LOCPROPS_NAMES, dtype='object')
        for (gwcol, dncol) in self.MAPPING_LOCPROPS.items():
            if not _pd.isnull(dncol):
                locprops[gwcol]=self._wellprops.loc[0, dncol]

        tubeprops = _pd.DataFrame(columns=GwSeries.TUBEPROPS_NAMES, dtype='object')
        for (gwcol, dncol) in self.MAPPING_TUBEPROPS.items():
            if not _pd.isnull(dncol):
                tubeprops.loc[0, gwcol]=self._wellprops.loc[0, dncol]

        heads = _pd.DataFrame(columns=GwSeries.HEADPROPS_NAMES, dtype='object')
        for (gwcol, dncol) in self.MAPPING_HEADPROPS.items():
            heads[gwcol] = self._obs[dncol]

        # from cm to m
        heads['headmp'] = heads['headmp']/100.
        for column in ['mplevel', 'filtop', 'filbot', 'surfacelevel']:
            tubeprops[column] = tubeprops[column]/100

        return GwSeries(heads=heads, locprops=locprops, tubeprops=tubeprops)


    def _check_expected_columns(self):
        """Check for changes in expected column names."""

        for gwcols, mapping in [
            (GwSeries.LOCPROPS_NAMES, self.MAPPING_LOCPROPS),
            (GwSeries.TUBEPROPS_NAMES, self.MAPPING_TUBEPROPS),
            ]:

            unknown_columns = [x for x in mapping.keys() 
                if x not in gwcols]
            if unknown_columns:
                raise InputError(f'Mapping contains column names not in '
                    f'GwSeries: {unknown_columns}')

            missing_columns = [x for x in gwcols 
                if x not in mapping.keys()]
            if unknown_columns:
                raise InputError(f'Mapping contains column names not in '
                    f'GwSeries: {unknown_columns}')


class BroDataDinoGwlCollection:
    """Download dino groundwater level data from dinoloket."""

    def __init__(self, dinogdf):
        self._dinogdf = dinogdf

    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'

    def __len__(self):
        return len(self._dinogdf)

    @classmethod
    def from_rectangle(cls, xmin=None, xmax=None, ymin=None, ymax=None,
        title=None):
        """Get all BRO well tubes within a rectangular area.
        
        Parameters
        ----------
        xmin : float
            Xcoor left boundary in Dutch RD coordinates.
        xmax : float
            Xcoor right boundary in Dutch RD coordinates.
        ymin : float
            Ycoor lower boundary in Dutch RD coordinates.
        ymax : float
            Ycoor upper boundary in Dutch RD coordinates.
        title : str, optional
            User defined name for collection.

        Returns
        -------
        BroGwCollection
                        
        """
        #extent = [271500, 272000, 551240, 551600]
        extent = [xmin, xmax, ymin, ymax]
        dinogdf = _brodata.dino.get_grondwaterstand(
            extent=extent, timeout=500, redownload=False, ) #max_retries=10)
        if not isinstance(dinogdf, _gpd.GeoDataFrame):
            raise ValueError(f'Request from Dino returned {dinogdf.__class__.__name__} not GeoDataFrame.')

        return BroDataDinoGwlCollection(dinogdf)

    @property
    def empty(self):
        if self._dinogdf.empty:
            return True
        return False


    def items(self):
        return list(self._dinogdf.index.values)


    def gwseries(self, nitgcode, tube):
        """Return GwSeries for (nitgnr, tube)."""

        obs = self._dinogdf.loc[(nitgcode, tube), 'data']
        meta = self._dinogdf.loc[(nitgcode, tube), 'meta']
        request = _pd.Series()
        for column in ['Periode aangevraagd:', 'Gegevens beschikbaar:', 
            'Datum:', 'Referentie:']:
            request[column]=self._dinogdf.loc[(nitgcode, tube), column]

        brodinogwl = BroDataDinoGwl.from_nitgcode(nitgcode, tube)
        gw = brodinogwl.gwseries()
        return gw


    def iteritems(self):
        """Iterate over well tubes and return gwseries object."""

        for (nitgcode, tube) in self._dinogdf.index:
            gw = self.gwseries(nitgcode, tube)
            yield gw

