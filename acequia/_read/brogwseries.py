
import warnings
from pandas import Series, DataFrame
import pandas as pd
from .brogmwxml import BroGmwXml
from .brogldxml import BroGldXml
from . import brorest
from .._core.gwseries import GwSeries

class BroGwSeries:
    """BRO groundwaterlevel series."""

    def __init__(self, wellprops=None, wellevents=None, 
        tubeprops=None, gldprops=None, obsprops=None, obs=None, 
        procesprops=None, timeseriescounts=None, gmwid=None, 
        tube=None):

        self._wellprops = wellprops
        self._wellevents = wellevents
        self._tubeprops = tubeprops
        self._gldprops = gldprops
        self._obsprops = obsprops
        self._obs = obs
        self._procesprops = procesprops
        self._timeseriescounts = timeseriescounts
        self.gmwid = gmwid
        self.tube = tube

    def __repr__(self):
        if self.empty:
            return f'{self.__class__.__name__} (empty)'
        return f'{self.seriesname} (n={len(self)})'

    def __len__(self):
        return len(self.observations)

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
        gmwid = gmw.gmwid
        tube = gld.tubeid

        # get properties from gmw
        tubeprops, wellprops, wellevents = cls._get_gmw_properties(gmw, tube)

        # select one filter from tubeprops
        #tubeprops = tubeprops[tubeprops['tubeNumber']==tube]
        #tubeprops = tubeprops.T.squeeze()
        #tubeprops.name = gmw.gmwid

        # get properties from gld
        gldprops, obs, obsprops, procesprops, timeseriescounts = cls._get_gld_properties([gld])

        return cls(wellprops=wellprops, wellevents=wellevents, 
            tubeprops=tubeprops, gldprops=gldprops, obsprops=obsprops,
            obs=obs, procesprops=procesprops, 
            timeseriescounts=timeseriescounts,
            gmwid=gmwid, tube=tube
            )

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


        """
        tuberef = brorest.get_welltubes(gmwid)
        gldid = tuberef.loc[tube,'gldid']

        gld = BroGldXml.from_server(gldid)
        gmw = BroGmwXml.from_server(gmwid)

        return cls(gld=gld, gmw=gmw)
        """

        gmw = BroGmwXml.from_server(gmwid)
        if gmw._tree is None:
            warnings.warn((f"Invalid XML tree for {gmwid} tube {tube}."))
            return cls(wellprops=Series(), wellevents=DataFrame(), 
                tubeprops=Series, gldprops=DataFrame, obsprops=DataFrame(), 
                obs=DataFrame(), procesprops=DataFrame(), 
                timeseriescounts=DataFrame(), gmwid=gmwid, tube=tube)

        # parse gmw xml tree
        tubeprops, wellprops, wellevents = cls._get_gmw_properties(gmw, tube)

        # get all gld xmls from REST server
        tube = str(tube)
        tubegld = brorest.get_welltubes(gmwid)
        tubegld = tubegld.loc[[tube],:].copy()
        gldxml = []
        for gldid in tubegld['gldid'].values:
            gld = BroGldXml.from_server(gldid)
            if gld._tree is not None:
                gldxml.append(gld)
            else:
                warnings.warn((f"Invalid GLDXML for {gldid} of {gmwid}."))

        # parse gld xml tree
        if gldxml: 
            gldprops, obs, obsprops, procesprops, timeseriescounts = cls._get_gld_properties(gldxml)
        else: # no valid GLD found for this tube
            gldprops = Series
            obs = DataFrame()
            obsprops = DataFrame()
            procesprops = DataFrame()
            timeseriescounts = DataFrame()
            warnings.warn((f'No valid GLD found for {gmwid} tube {tube}.'))

        return cls(wellprops=wellprops, wellevents=wellevents, 
            tubeprops=tubeprops, gldprops=gldprops, obsprops=obsprops,
            obs=obs, procesprops=procesprops, 
            timeseriescounts=timeseriescounts, gmwid=gmwid, tube=tube
            )

    @classmethod
    def _get_gmw_properties(cls, gmw, tube):
        """Return properties of gmw object."""

        # tube properties
        tubeprops = gmw.tubeprops.loc[[str(tube)],:]
            # .loc with double brackets allways returns a dataframe
        tubeprops.insert(0, gmw.tubeprops.index.name, tubeprops.index)
        tubeprops = tubeprops.reset_index(drop=True).squeeze()
        tubeprops.name = gmw.gmwid

        # well properties
        wellprops = gmw.wellprops

        # well events
        wellevents = gmw.events
        wellevents['gmwid'] = gmw.gmwid

        return tubeprops, wellprops, wellevents

    @classmethod
    def _get_gld_properties(cls, gldxml):
        """Get properties from list of GLD objects."""

        # get props for each GLD and concatenate
        gldprops = []
        obsprops = []
        procesprops = []
        timeseriescounts = []
        obs = []
        heads = []
        for gld in gldxml:

            # get gldprops
            gldprops.append(gld.gldprops)

            # get obsprops
            df = gld.obsprops
            df['gldid'] = gld.gldid
            obsprops.append(df)
            
            # get procesprops
            df = gld.procesprops
            df['gldid'] = gld.gldid
            procesprops.append(df)
            
            # get timeseriescounts
            sr = gld.timeseriescounts
            sr.name = 'counts'
            df = DataFrame(sr)
            df.index.name = 'timeseries'
            df['gldid'] = gld.gldid
            timeseriescounts.append(df)

            # get obs
            df = gld.obs
            df['gldid'] = gld.gldid
            obs.append(df)

        # create pandas dataframes
        gldprops = pd.concat(gldprops, axis=1).T.set_index('broIdGld')
        obsprops = pd.concat(obsprops)
        procesprops = pd.concat(procesprops).reset_index(drop=True)
        timeseriescounts = pd.concat(timeseriescounts)
        obs = pd.concat(obs).reset_index(drop=True)
        
        return gldprops, obs, obsprops, procesprops, timeseriescounts

    @property
    def empty(self):

        if self._wellprops.empty:
            return True
        if self._tubeprops.empty:
            return True
        if self._obs.empty:
            return True
        if self.gwseries.heads().empty:
            return True
        return False

    #@property
    #def tube(self):
    #    return self._tubeprops['tubeNumber']

    @property
    def tubeprops(self):
        return self._tubeprops ##.loc[self.tube,:]

    @property
    def wellprops(self):
        return self._wellprops

    @property
    def ownerid(self):
        return self._wellprops['deliveryAccountableParty']

    @property
    def wellcode(self):
        return str(self._wellprops['wellCode'])

    @property
    def nitgcode(self):
        return self._wellprops['nitgCode']

    @property
    def seriesname(self):
        return f'{self.wellcode}_{self.tube}'

    @property
    def observations(self):
        return self._obs

    @property
    def heads(self):
        """Return time series with groundwater levels."""
        if self._obs.empty:
            return Series(dtype='object')

        levels = self._obs['value'].astype(float).values
        datetimes = pd.DatetimeIndex(
            pd.to_datetime(self._obs['time'],
            utc=True)).tz_localize(None)
        name = self.gmwid
        heads = Series(data=levels, index=datetimes, name=name)
        if heads.index.has_duplicates:
            dupcount = len(heads[heads.index.duplicated(keep='first')])
            heads = heads[~heads.index.duplicated(keep='first')].copy()
        return heads.sort_index()

    @property
    def gwseries(self):
        gw = GwSeries()
        
        
        
        # locprops
        gw._locprops['locname'] = self.gmwid
        gw._locprops['filname'] = self.tube
        gw._locprops['alias'] = self.wellcode
        gw._locprops['xcr'] = self._wellprops['xcr']
        gw._locprops['ycr'] = self._wellprops['ycr']
        gw._locprops['height_datum'] = self._wellprops['verticalDatum']
        gw._locprops['grid_reference'] = self._wellprops['coordinateTransformation']
        #gw._locprops['observer'] = self.wellprops['deliveryAccountableParty']
        #gw._locprops['owner'] = self.wellprops['owner']
        #gw._locprops['wellconstructiondate'] = self.wellprops['wellConstructionDate']

        # tubeprops
        startdate = self.heads.index.min() # timestamp
        """
        if pd.isnull(startdate):
            raise ValueError((f'No heads series start date found in '
                f'well {self.gmwid} filter {self.tube}.'))
        """
        """
        startdate = self._wellprops['wellConstructionDate'] # timestamp
        if pd.isnull(self._wellprops.loc['wellConstructionDate']):
            startdate = self.heads.index.min() # timestamp
            warnings.warn((f'Tube {self.tube} of {self.gmwid} has no '
                f'well construction date. Startdate '
                f'{startdate.strftime('%d-%m-%Y')} is based on heads series.'))
        """
        
        gw._tubeprops.loc[1,'series'] = self.seriesname
        gw._tubeprops.loc[1,'startdate'] = startdate
        gw._tubeprops.loc[1,'mplevel'] = self._tubeprops['tubeTopPosition']
        gw._tubeprops.loc[1,'filtop'] = self._tubeprops['screenTopPosition']
        gw._tubeprops.loc[1,'filbot'] = self._tubeprops['screenBottomPosition']
        #gw._tubeprops.loc[1,'surfacedate'] = None
        gw._tubeprops.loc[1,'surfacelevel'] = self._wellprops['groundLevelPosition']
        #gw._tubeprops.loc[1,'surfaceprecision'] = self.wellprops['groundLevelPositioningMethod']

        if self.heads.empty:
            warnings.warn((f'Empty series for {self.seriesname}.'))
            return gw

        # heads
        gw._obs['headdatetime'] = self.heads.index.values
        gw._obs['headmp'] = self.tubeprops['tubeTopPosition'] - self.heads.values
        gw._obs = gw._obs.reset_index(drop=True)

        return gw
