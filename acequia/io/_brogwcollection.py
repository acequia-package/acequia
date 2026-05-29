
import warnings
import os as _os
##from pandas import Series, DataFrame
import pandas as _pd
import geopandas as _gpd

from ._brorest import BroREST
from ._brogwseries import BroGwSeries
from .._core.gwseries import GwSeries

from ..tools import convert_RDtoWGS84
from ..data import bro_instanties

def brogmw_from_rectangle(xmin=None, xmax=None, ymin=None, 
    ymax=None, title=None):
    """Get all BRO well tube levels within a rectangular area.
    
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
    broc = BroGwCollection()
    gwc = broc.from_rectangle(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
        title=title)
    return gwc


class BroGwCollection:
    """Collection of BRO groundwater well tubes."""


    def __init__(self, gmw=None, gld=None, title=None):

        self._gmw = gmw
        self._gld = gld
        self.title = title


    def __repr__(self):
    
        name = self.title
        if name is None:
            name = 'BroGwCollection'
        return f'{name} (n={len(self)})'


    def __len__(self):
        return len(self.tubes())


    @classmethod
    def from_rectangle(cls, xmin=None, xmax=None, ymin=None, ymax=None,
        startdate=None, enddate=None, title=None):
        """Get all BRO well tube levels within a rectangular area.
        
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
        startdate : str, default '2001-01-01'
            Minimum value of well registration date.
        enddate : str, default today
            Maximum value of well registration date. 
        title : str, optional
            User defined name for collection.

        Returns
        -------
        BroGwCollection
           
        """

        brest = BroREST()
        gmws = brest.get_gmwcodes_from_area(
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, 
            startdate=startdate, enddate=enddate, 
            description=title,
            )

        if gmws.empty:
            return cls(gmws=_pd.DataFrame(), glds=_pd.DataFrame(), title=title)

        glds = []
        for gmwid in gmws['gmwid'].values:
            gmwgld = brest.get_gld_from_gmw(gmwid)
            if gmwgld.empty:
                continue
            gmwgld.insert(1,'tubenr', gmwgld.index.values)
            glds.append(gmwgld)
        glds = _pd.concat(glds).reset_index(drop=True)

        return cls(gmw=gmws, gld=glds, title=title)


    def wellprops(self, geo=True):
        wells = self._gmw.set_index('gmwid', verify_integrity=True)
        wells = wells.rename(columns={'filshallow':'tube_shallow','fildeep':'tube_deep'})

        # split xy
        wells['xcr'] = wells['xy'].str.split(' ', expand=True)[0]
        wells['ycr'] = wells['xy'].str.split(' ', expand=True)[1]

        # strings to float
        for col in ['surfacelevel','tube_shallow', 'tube_deep',]:
            wells[col] = wells[col].astype('float')
        wells['maxdepth']=wells['surfacelevel']-wells['tube_deep']

        # replace instantie id with name
        for col in ['accountable', 'owner']:
            wells[col] = wells[col].map(bro_instanties())

        wells = wells.drop(columns=['latlon','xy','registrationtime','correctiontime',])

        if geo:
            # to godataframe
            geom = _gpd.points_from_xy(wells['xcr'], wells['ycr'], crs="EPSG:28992")
            wells = _gpd.GeoDataFrame(wells, geometry=geom)

        return wells


    @property
    def empty(self):
        if self._gmw.empty | self._gld.empty:
            return True
        return False


    def wells(self):
        """Return list of location names."""
        return list(self._gld['gmwid'].unique())


    def tubes(self):
        """List of all series names."""
        mask = ~self._gld.duplicated(subset=['gmwid','tubenr'], keep='last')
        tubes = self._gld[mask][['gmwid','tubenr']]
        tubes = zip(tubes['gmwid'], tubes['tubenr'])
        tubenames = [x[0]+"_"+x[1] for x in tubes]
        return tubenames


    def gwseries(self, name):
        """Get gwseries for one well tube.
        
        Parameters
        ----------
        serie : str
            Series name as returned by tubes().

        Returns
        -------
        GwSeries
           
        """
        gmwid, tube = name.split('_')
        gw = BroGwSeries.from_server(gmwid=gmwid, tube=tube)
        return gw.gwseries


    def iteritems(self):
        """Iterate over all well tube series and return gwseries object."""

        for name in self.tubes():
            gw = self.gwseries(name)
            yield gw


    def __iter__(self):

        for name in self.tubes():
            gw = self.gwseries(name)
            yield gw


    def to_folder(self, folder):
        """Save groundwater series to folder as json files 
        (skip empty series)."""
        
        if not isinstance(folder, str):
            raise ValueError((f"Variable folder must be a string with "
                f"a valid folder name, not '{folder}',"))

        # create folder
        try:
            _os.mkdir(folder)
        except FileExistsError:
            pass

        # save gwseries to json
        for gw in self:
            if not gw.empty:
                gw.to_json(folder)

