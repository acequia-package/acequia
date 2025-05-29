"""Module with object for managing HydroPandas ObsCollection object.

Note
----
HydroPandas is not a dependency of Acequia. This module assumes that 
a HydroPandas ObsCollection instance is somehowe available, which implies 
that the user has installed hydropandas.
        
"""

from pandas import Series, DataFrame
import pandas as pd
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
    gwo = HydropandasGroundwaterObservations(obs)
    gws = gwo.get_gwseries(include_missing_heads=include_missing_heads)
    return gws
    

def get_gwcollection_from_pandas(obscollection):

    gwc = HydropandasObsCollection(obscollection)
    return gwc


class HydropandasGroundwaterObservations:
    """Manage Hydropandas GroundwaterObservations object."""

    HYDROPANDAS_CLASS_NAME = 'GroundwaterObs'

    MAPPING_HYDROPANDAS_LOCPROPS = {
        'locname' : 'monitoring_well',
        'filname' : 'tube_nr',
        'alias' : None,
        'xcr' : 'x',
        'ycr' : 'y',
        'height_datum' : 'unit',
        'grid_reference' : None,
        }

    MAPPING_HYDROPANDAS_TUBEPROPS = {
        'startdate':None,
        'mplevel':'tube_top',
        'filtop':'screen_top',
        'filbot':'screen_bottom',
        'surfacedate':None, 
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


    def __len__(self):
        return len(self._obs.index)


    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'

    def get_gwseries(self, include_missing_heads=True):
        """Return GwSeries object."""

        # get locprops
        locprops = Series(index=GwSeries().LOCPROPS_NAMES, dtype='object')
        for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_LOCPROPS.items():
            if hpdkey is not None:
                locprops[gwkey] = self._obs.__dict__[hpdkey]
        locprops['grid_reference'] = 'RD'

        # get tubeprops
        tubeprops = DataFrame(columns=GwSeries().TUBEPROPS_NAMES)
        for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_TUBEPROPS.items():
            if hpdkey is not None:
                tubeprops.loc[0, gwkey] = self._obs.__dict__[hpdkey]
        if not self._obs.empty:
            tubeprops.loc[0,'startdate'] = self._obs.index[0]

        for col in GwSeries().TUBEPROPS_NUMCOLS:
            tubeprops[col] = pd.to_numeric(
                tubeprops[col], errors='coerce')

        # get head observations
        heads = DataFrame(columns=GwSeries().HEADPROPS_NAMES)
        if not self._obs.empty:
            hpd_obs = self._obs.reset_index() # datetime is index
            if not include_missing_heads:
                # remove empty head observations
                hpd_obs = hpd_obs[~pd.isnull(hpd_obs['value'])].copy()

            # get headprops
            for gwkey, hpdkey in self.MAPPING_HYDROPANDAS_HEADPROPS.items():
                heads[gwkey]=hpd_obs[hpdkey]

            # heads from nap to refmp
            if len(tubeprops)>1:
                raise ValueError((f'Table with tubeprops contains more than one entry. '
                    f'Recalculation of heads from NAP to MP not supported.'))
            heads['headmp'] = tubeprops.loc[0,'mplevel']-heads['headmp']

        return GwSeries(heads=heads, locprops=locprops, tubeprops=tubeprops)


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
        self._obscol = obscollection
        self._iternames = self.names

    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self)})')


    def __len__(self):    
        return len(self._obscol['obs'])

    @property
    def empty(self):
        if len(self)==0:
            return True
        return False

    @property
    def names(self):
        """Return list of series names."""
        return list(self._obscol['obs'].index.values)

    @property
    def loclist(self):
        return list(self._obscol.monitoring_well.values)


    def get_gwseries(self, seriesname):
        """Return GwSeries object.
        
        Parameters
        ----------
        seriesname : str
            Valid name for series in collection.
            
        Returns
        -------
        GwSeries
            
        """
        obs = self._obscol.loc[seriesname,'obs']
        hgo =  HydropandasGroundwaterObservations(obs)
        gw = hgo.get_gwseries()
        return gw


    def iteritems(self):
        """Iterate over all series in collecion and return gwseries 
        object."""
        names = self.names
        while len(names)>0:
            seriesname = names.pop(0)
            gw = self.get_gwseries(seriesname)
            yield gw


    def __next__(self):
        while len(self._iternames)>0:
            seriesname = self._iternames.pop(0)
            gw = self.get_gwseries(seriesname)
            return gw
        self._iternames = self.names # reset for next Iteration call
        raise StopIteration


    def __iter__(self):
        return self

