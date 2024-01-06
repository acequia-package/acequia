
import warnings
from pandas import Series, DataFrame
import pandas as pd

from . import brorest
from .brogwseries import BroGwSeries
from .._core.gwseries import GwSeries

from .._geo.coordinate_conversion import convert_RDtoWGS84

class BroGwCollection:
    """Collection of BRO groundwater well tubes."""

    def __init__(self, wells=None, tubes=None, name=None):

        self._wells = wells
        self._tubes = tubes
        self.name = name

    def __repr__(self):
    
        name = self.name
        if name is None:
            name = 'BroGwCollection'
            
        return f'{name} (n={len(self)})'

    def __len__(self):
        return len(self._tubes)

    @classmethod
    def from_rectangle(cls, xmin=None, xmax=None, ymin=None, ymax=None,
        name=None):
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
            return cls(wells=DataFrame(), tubes=DataFrame(), name=name)

        tubes = []
        for gmwid in wells['gmwid'].values:
            welltubes = brorest.get_welltubes(gmwid)
            if welltubes.empty:
                continue
            welltubes.insert(1,'tubenr',welltubes.index.values)
            tubes.append(welltubes)
        tubes = pd.concat(tubes).reset_index(drop=True)

        return cls(wells=wells, tubes=tubes, name=name)

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

    def get_gwseries(self, gmwid=None, wellcode=None, tube=None):
        """Get gwseries for one well tube.
        
        Parameters
        ----------
        gmwid : str | int
            Valid BRO GMW well ID.
        wellcode : str, optional
            Valid wellcode (alternative to Gmwid).
        tube : str | int
            Well tube id.

        Returns
        -------
        GwSeries
           
        """
        # get gmwid from wellcode
        if isinstance(wellcode, str):
            wellcodes = self._wells[self._wells['wellcode']==wellcode]
            if not wellcodes.empty:
                idx = wellcodes.index[0]
                gmwid = self._wells.loc[idx, 'gmwid']
            else:
                # wellcode not found
                warnings.warn((f'Wellcode {wellcode} not found.'
                    f'in collection {self.name}.'))
                return GwSeries()

        bros = BroGwSeries.from_server(gmwid=gmwid, tube=tube)
        return bros.gwseries

    def iteritems(self):
        """Iterate over all well tube series and return gwseries object."""

        for idx, row in self._tubes.iterrows():
            gw = self.get_gwseries(gmwid=row['gmwid'], tube=row['tubenr'])
            yield gw
