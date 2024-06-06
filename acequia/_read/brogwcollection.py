
import warnings
from pandas import Series, DataFrame
import pandas as pd

from . import brorest
from .brogwseries import BroGwSeries
from .._core.gwseries import GwSeries

from .._geo.coordinate_conversion import convert_RDtoWGS84

class BroGwCollection:
    """Collection of BRO groundwater well tubes."""

    def __init__(self, wells=None, tubes=None, title=None):

        self._wells = wells
        self._tubes = tubes
        self.title = title

    def __repr__(self):
    
        name = self.title
        if name is None:
            name = 'BroGwCollection'
            
        return f'{name} (n={len(self)})'

    def __len__(self):
        return len(self._tubes)

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
        name : str, optional
            User defined name for collection.

        Returns
        -------
        BroGwCollection
           
        """
        lowerleft = convert_RDtoWGS84(xmin, ymin)
        upperright = convert_RDtoWGS84(xmax, ymax)

        wells = brorest.get_area_wellprops(
            lowerleft=lowerleft, 
            upperright=upperright,
            )

        if wells.empty:
            return cls(wells=DataFrame(), tubes=DataFrame(), title=title)

        tubes = []
        for gmwid in wells['gmwid'].values:
            welltubes = brorest.get_welltubes(gmwid)
            if welltubes.empty:
                continue
            welltubes.insert(1,'tubenr',welltubes.index.values)
            tubes.append(welltubes)
        tubes = pd.concat(tubes).reset_index(drop=True)

        return cls(wells=wells, tubes=tubes, title=title)

    @property
    def wells(self):
        return self._wells

    @property
    def tubes(self):
        return self._tubes

    @property
    def empty(self):
        if self.wells.empty | self.tubes.empty:
            return True
        return False

    @property
    def loclist(self):
        """Return list of location names."""
        return list(set(self._tubes['gmwid'].values))


    @property
    def names(self):
        """List of all series names."""
        gmwtube = zip(self._tubes['gmwid'].values, self._tubes['tubenr'].values)
        names = [x[0]+"_"+x[1] for x in gmwtube]
        return names

    def get_gwseries(self, name):
        """Get gwseries for one well tube.
        
        Parameters
        ----------
        serie : str
            Series name as in property "names".

        Returns
        -------
        GwSeries
           
        """
        gmwid, tube = name.split('_')
        gw = BroGwSeries.from_server(gmwid=gmwid, tube=tube)
        return gw.gwseries

    def iteritems(self):
        """Iterate over all well tube series and return gwseries object."""

        for name in self.names:
            gw = self.get_gwseries(name)
            #if len(gw)==0:
            #    warnings.warn((f'Skipped {gw.name()} with no measurements.'))
            #    continue
            yield gw
