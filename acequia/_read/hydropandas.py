"""Module with object for managing HydroPandas ObsCollection object.

Note
----
HydroPandas is not a dependency of Acequia. This module assumes that 
a HydroPandas ObsCollection instance is somehowe available, which implies 
that the user has installed hydropandas.
        
"""

import numpy as _np
from pandas import Series, DataFrame
import pandas as _pd
from .._core.gwseries import GwSeries


def get_gwseries_from_hydropandas(obs, include_missing_heads=True):
    """Return GwSeries object from Hydropandas Groundwater Observations object.
    
    Parameters
    ----------
    obs : hydropandas GroundwatrerObs
        Groundwaterheads data from hydropandas.

    include_missing_heads : bool, default True
        Return missing head observation entries (True) or not (False).

    Returns
    -------
    GwSeries
        Groundwater tube and heads data.
            
    """
    gwobs = HydropandasGroundwaterObs(obs)
    gws = gwobs.get_gwseries(include_missing_heads=include_missing_heads)
    return gws
    

def get_gwcollection_from_pandas(obscollection):

    gwc = HydropandasObsCollection(obscollection)
    return gwc


class HydropandasGroundwaterObs:
    """Manage Hydropandas GroundwaterObservations object."""

    HYDROPANDAS_CLASS_NAME = 'GroundwaterObs'

    MAPPING_HYDROPANDAS_LOCPROPS = {
        'locname' : 'location',
        'filname' : 'tube_nr',
        'alias' : _np.nan,
        'alias2' : _np.nan,
        'owner' : _np.nan,
        'observer' : _np.nan,
        'constructiondate' : _np.nan,
        'surfacestable' : _np.nan,
        'xcr' : 'x',
        'ycr' : 'y',
        'height_datum' : 'unit',
        'grid_reference' : _np.nan,
        }


    MAPPING_HYDROPANDAS_TUBEPROPS = {
        'startdate':_np.nan,
        'mplevel':'tube_top',
        'filtop':'screen_top',
        'filbot':'screen_bottom',
        'surfacedate':_np.nan, 
        'surfacelevel':'ground_level',
        }

    MAPPING_HYDROPANDAS_HEADPROPS = {
        'headdatetime':'peil_datum_tijd', 
        'headmp':'value',
        'headnote':'flag',
        'remarks':'comment',
        }

    def __init__(self, obs):
        """
        Parameters
        ----------
        obscollection : Hydropandas Obscollection.
            Groundwaterhead observations for multiple groundwater tubes.

        Returns
        -------
        HydropandasGroundwaterObservations
            
        """
        if not obs.__class__.__name__==self.HYDROPANDAS_CLASS_NAME:
            raise ValueError((f'Variable obscollection must be a pandas'
                f'ObsCollection object. Not '
                f'{obs.__class__.__name__}.')
                )
        self._obs = obs

        # check for code changes in MAPPING keys
        # locprops
        gwkeys = GwSeries.LOCPROPS_NAMES
        mapkeys = self.MAPPING_HYDROPANDAS_LOCPROPS.keys()
        self._check_mapkeys(gwkeys, mapkeys)
        # tubeprops
        gwkeys = GwSeries.TUBEPROPS_NAMES
        mapkeys = self.MAPPING_HYDROPANDAS_TUBEPROPS.keys()
        self._check_mapkeys(gwkeys, mapkeys)


    def __len__(self):
        return len(self._obs.index)


    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'


    def _check_mapkeys(self, gwkeys, mapkeys):
        """Check if keys in MAPPINGS are correct and complete."""
        missing_mapkeys = [x for x in gwkeys if x not in mapkeys]
        unknown_mapkeys = [x for x in mapkeys if x not in gwkeys]
        if missing_mapkeys:
            raise ValueError(f'Missing keys in locprops mapping: {missing_mapkeys}.')
        if unknown_mapkeys:
            raise ValueError(f'Unknown keys in locprops mapping: {unknown_mapkeys}.')


    def locprops(self):
        locprops = Series(index=GwSeries().LOCPROPS_NAMES, dtype='object')
        obsdict = self._obs.__dict__
        for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_LOCPROPS.items():
            if not _pd.isnull(hpdkey):
                locprops[gwkey] = obsdict[hpdkey]
        return locprops


    def tubeprops(self):
        tubeprops = DataFrame(columns=GwSeries().TUBEPROPS_NAMES)
        for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_TUBEPROPS.items():
            if not _pd.isnull(hpdkey):
                tubeprops.loc[0, gwkey] = self._obs.__dict__[hpdkey]
        if not self._obs.empty:
            tubeprops.loc[0,'startdate'] = self._obs.index[0]

        for col in GwSeries().TUBEPROPS_NUMCOLS:
            tubeprops[col] = _pd.to_numeric(
                tubeprops[col], errors='coerce')
        return tubeprops


    def obs(self, include_missing_heads=True, include_unreliable=False):

        # get head observations
        heads = DataFrame(columns=GwSeries().HEADPROPS_NAMES)
        if self._obs.empty:
            return heads

        hpd_obs = self._obs.reset_index() # datetime is index

        if not include_missing_heads:
            # remove empty head observations
            obs_not_missing = ~_pd.isnull(hpd_obs['value'])
            hpd_obs = hpd_obs[obs_not_missing].copy()

        if not include_unreliable:
            unreliable_obs = hpd_obs['flag']=='onbetrouwbaar'   
            hpd_obs = hpd_obs[~unreliable_obs].copy()

        # get headprops
        for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_HEADPROPS.items():
            heads[gwkey]=hpd_obs[hpdkey]

        # convert heads from nap to refmp
        tubeprops = self.tubeprops()
        if len(tubeprops)>1:
            raise ValueError((f'Table with tubeprops contains more than one row. '
                f'Recalculation of heads from NAP to MP for tubes with history'
                f'is not supported.'))
        mp = tubeprops.loc[0,'mplevel']

        heads['headmp'] = mp-heads['headmp']

        return heads


    def get_gwseries(self, include_missing_heads=True, 
        include_unreliable=False):
        """Return GwSeries object."""

        # get locprops
        locprops = self.locprops()

        # get tubeprops
        tubeprops = self.tubeprops()

        # get obs
        obs = self.obs(include_missing_heads=include_missing_heads, 
            include_unreliable=include_unreliable)

        return GwSeries(heads=obs, locprops=locprops, tubeprops=tubeprops)


class HydropandasObsCollection:
    """Manage Hydropandas ObsCollection object."""


    def __init__(self, obscollection):
        """
        Parameters
        ----------
        obscollection : Hydropandas Obscollection.
            Groundwaterhead observations for multiple groundwater tubes.
            
        """
        if not obscollection.__class__.__name__=='ObsCollection':
            raise ValueError((f'Variable obscollection must be a pandas'
                f'ObsCollection object. Not '
                f'{obscollection.__class__.__name__}.')
                )
        self._hpd_obscollection = obscollection
        self.obs = self._hpd_obscollection.obs
        ##self._seriesnames = self.obscol.index.values
        
        # used for iterations
        self._iternames = [x for x in self.names]

    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self)})')


    def __len__(self):    
        return len(self.obs)


    @property
    def empty(self):
        if len(self)==0:
            return True
        return False


    @property
    def names(self):
        """Return list of series names."""
        ## return list(self._obscol['obs'].index.values)
        return self.obs.index.values


    @property
    def loclist(self):
        locationtable = self._hpd_obscollection.location
        return locationtable.values


    def get_gwseries(self, seriesname, include_missing_heads=True, 
        include_unreliable=False):
        """Return GwSeries object.
        
        Parameters
        ----------
        seriesname : str
            Valid name for series in collection.
            
        Returns
        -------
        GwSeries
            
        """
        series = self.obs[seriesname]
        gwobs =  HydropandasGroundwaterObs(series)
        gw = gwobs.get_gwseries(include_missing_heads=include_missing_heads, 
        include_unreliable=include_unreliable)
        return gw


    def iteritems(self):
        """Iterate over all series in collecion and return gwseries 
        object."""
        names = [x for x in self.names]
        while len(names)>0:
            seriesname = names.pop(0)
            gw = self.get_gwseries(seriesname)
            yield gw


    def __next__(self):
        
        while len(self._iternames)>0:
            seriesname = self._iternames.pop(0)
            gw = self.get_gwseries(seriesname)
            return gw
        # reset iternames for next iteration
        self._iternames = [x for x in self.names]
        raise StopIteration 


    def __iter__(self):
        return self

