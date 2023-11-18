
from pandas import Series, DataFrame
import pandas as pd
from .brogmwxml import BroGmwXml
from .brogldxml import BroGldXml
from . import brorest
from .._core.gwseries import GwSeries

class BroGwSeries:
    """BRO groundwaterlevel series."""

    def __init__(self, gld=None, gmw=None):

        self._gld = gld
        self._gmw = gmw
        ##self._tube = tube

    def __repr__(self):
        return f'{self.seriesname} (n={len(self)})'

    def __len__(self):
        return len(self._gld.heads)

    @classmethod
    def from_files(cls, gmwpath=None, gldpath=None):
        """Read groundwater level data from BRO XML files.
        
        Parameters
        ----------
        gmwpath : str
            Path to XML file with BRO GMW data.

        gldpath : str
            Path to XML file with BRO GLD data.
        tubenr : str | int
            Well tube id. 
            
        Returns
        -------
        BroGwSeries """

        gmw = BroGmwXml.from_xml(gmwpath)
        gld = BroGldXml.from_xml(gldpath)
        return cls(gld=gld, gmw=gmw)

    @classmethod
    def from_server(cls, gmwid=None, tube=None):
        """Download data with BRO REST service.

        Parameters
        ----------
        GmwID : str
            Valid BRO GMW well ID.
        tube : str | int
            Well tube id.

        Returns
        -------
        BroGwSeries """
        tube = str(tube)
        
        tuberef = brorest.get_welltubes(gmwid)
        gldid = tuberef.loc[tube,'gldid']

        gld = BroGldXml.from_server(gldid)
        gmw = BroGmwXml.from_server(gmwid)

        return cls(gld=gld, gmw=gmw)


    @property
    def gldid(self):
        return self._gld.gldprops['broIdGld']

    @property
    def tubeprops(self):
        return self._gmw.tubeprops.loc[self.tubeid,:].copy()

    @property
    def wellprops(self):
        return self._gmw.wellprops.copy()

    @property
    def tubeid(self):
        return self._gld.gldprops['tubeNumber']

    @property
    def gmwid(self):
        return self._gmw.wellprops['broId']

    @property
    def ownerid(self):
        return self._gmw.wellprops['deliveryAccountableParty']

    @property
    def wellcode(self):
        return str(self._gmw.wellprops['wellCode'])

    @property
    def nitgcode(self):
        return self._gmw.wellprops['nitgCode']

    @property
    def seriesname(self):
        return f'{self.wellcode}_{self.tubeid}'

    @property
    def gwseries(self):
        gw = GwSeries()
        
        # locprops
        gw._locprops['locname'] = self.wellprops['broId']
        gw._locprops['filname'] = self.tubeid
        gw._locprops['alias'] = self.wellprops['wellCode']
        gw._locprops['xcr'] = self.wellprops['xcr']
        gw._locprops['ycr'] = self.wellprops['ycr']
        gw._locprops['height_datum'] = self.wellprops['verticalDatum']
        gw._locprops['grid_reference'] = self.wellprops['coordinateTransformation']
        #gw._locprops['observer'] = self.wellprops['deliveryAccountableParty']
        #gw._locprops['owner'] = self.wellprops['owner']
        #gw._locprops['wellconstructiondate'] = self.wellprops['wellConstructionDate']

        # tubeprops
        gw._tubeprops.loc[1,'series'] = self.seriesname
        #datestring = self._gmw.wellprops['wellConstructionDate']
        #gw._tubeprops.loc[1,'startdate'] = dt.strptime(datestring, '%Y-%m-%d').date()
        gw._tubeprops.loc[1,'startdate'] = self.wellprops['wellConstructionDate']
        gw._tubeprops.loc[1,'mplevel'] = self.tubeprops['tubeTopPosition']
        gw._tubeprops.loc[1,'filtop'] = self.tubeprops['screenTopPosition']
        gw._tubeprops.loc[1,'filbot'] = self.tubeprops['screenBottomPosition']
        #gw._tubeprops.loc[1,'surfacedate'] = None
        gw._tubeprops.loc[1,'surfacelevel'] = self.wellprops['groundLevelPosition']
        #gw._tubeprops.loc[1,'surfaceprecision'] = self.wellprops['groundLevelPositioningMethod']

        # heads
        gw._heads['headdatetime'] = self._gld.heads.index.values
        gw._heads['headmp'] = self.tubeprops['tubeTopPosition'] - self._gld.heads.values
        gw._heads = gw._heads.reset_index(drop=True)

        return gw
