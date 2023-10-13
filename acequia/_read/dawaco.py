
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

from .._core.gwseries import GwSeries


class Dawaco:
    """Manage DAWACO ground water heads data set.

    Constructor
    -----------
    from_excel
        Read DAWACO hydroseries xlsx export file and return Dawaco object.
    ...
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
        'Datum_Tijd' : 'datetime',
        'Waarde (m -NAP)' : 'meas_nap',
        'Betrouwbaarheid' : 'reliabilty',
        }

    def __init__(self,rawdata=None,fpath=None,title=None):

        self.rawdata = rawdata
        self.fpath = fpath
        self.title = title

        self.rawdata = self.rawdata.rename(
            columns=self.COLUMNS_MAPPING, errors="raise")

    def __len__(self):
        seriescount = len(self.rawdata[['locname','filname']].drop_duplicates())
        return seriescount

    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'

    @classmethod
    def from_excel(cls, fpath, title=None):
        """Import Dawaco dataset from Excel export format."""
        rawdata = pd.read_excel(fpath,parse_dates=[['Datum','Tijd']])
        rawdata['Filter'] = rawdata['Filter'].astype(str)
        return cls(rawdata=rawdata, fpath=fpath, title=title)

    @property
    def filters(self):
        """Return list of tuples with (locname, filter) for all filters."""
        filters = self.rawdata[['locname','filname']].drop_duplicates()
        return list(zip(filters['locname'],filters['filname']))

    def get_gwseries(self,loc,fil):
        """Return data as list of Acequia GwSeries instances."""

        tbl = self.rawdata
        gw = GwSeries()

        # locprops
        idx = self.rawdata.index[0]
        gw._locprops['locname'] = loc
        gw._locprops['filname'] = fil
        gw._locprops['alias'] = np.nan
        gw._locprops['xcr'] = self.rawdata.loc[idx,'xcr']
        gw._locprops['ycr'] = self.rawdata.loc[idx,'ycr']
        gw._locprops['height_datum'] = 'NAP'
        gw._locprops['grid_reference'] = 'RD'

        # tubeprops
        tp = self.rawdata.copy()
        for col in gw.TUBEPROPS_NAMES:
            if col not in tp.columns:
                tp[col] = np.nan
        tp = tp[gw.TUBEPROPS_NAMES].drop_duplicates(keep='first',ignore_index=True)
        gw._tubeprops = tp.copy()

        # heads
        heads = gw._heads
        heads['headdatetime'] = self.rawdata['datetime']
        heads['headmp'] = self.rawdata['mplevel'] - self.rawdata['meas_nap']
        gw._heads = heads.reset_index(drop=True)

        return gw

    def iteritems(self):
        """Iterate over all groundwater head series and return gwseries objects."""

        for (loc,fil),tbl in self.rawdata.groupby(['locname','filname']):
            gw = self.get_gwseries(loc,fil)
            yield gw

