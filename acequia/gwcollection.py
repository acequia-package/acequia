"""
Module with GwCollection object holding a collection of groundwater 
head series.
"""

import warnings
from pandas import Series, DataFrame
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd

from .read.gwfiles import GwFiles

class GwCollection:
    """Collection of groundwater head series."""

    def __init__(self,gwcol):

        self.collection = gwcol
        self.stats = None
        self.xg = None
        self._ref = None
    
    @classmethod
    def from_dinocsv(cls,filedir):

        gwcol = GwFiles.from_dinocsv(filedir)
        return cls(gwcol)

    def iteritems(self):
        """Iterate over all series in collecion and return gwseries 
        object."""
        for gw in self.collection.iteritems():
            yield gw


    def _calculate_series_stats(self,ref='datum'):
        """Return table with series statistics.

        Parameters
        ----------
        ref : {'datum','surface','mp'}, default 'datum'
            head reference level
        """
        srstats_list = []
        xg_list = []
        for gw in self.iteritems():

            if not gw.tubeprops().empty:
                desc = gw.describe(ref=ref,gxg=True)
                srstats_list.append(desc)
                xg_list.append(gw.xg(ref=ref,name=True))
            else:
                warnings.warn((f'{gw.name()} has no tubeproperties ' 
                    f' and will be ignored.'))

        self.stats = pd.concat(srstats_list,axis=1).T
        self.stats.index.name = 'series'
        self.xg = pd.concat(xg_list,axis=0)
        self._ref = ref

    def get_wellfilterstats(self,ref='datum'):
        """Return statistics of measured heads for each well filter."""
    
        # recalculate stats if nessesary
        if (self.stats is None) | (self._ref!=ref):
            self._calculate_series_stats(ref=ref)


        xcr = self.stats['xcr'].astype('float').values
        ycr = self.stats['ycr'].astype('float').values
        geometry = [Point(crd) for crd in zip(xcr,ycr)]
        points = gpd.GeoDataFrame(self.stats, geometry=geometry)
        points = points.set_crs('EPSG:28992')

        for colname in ['firstdate','lastdate',]:
            points[colname] = points[colname].apply(lambda x:x.strftime('%d-%m-%Y'))
 
        return points




    def get_xg(self,ref='datum'):
    
        # recalculate stats if nessesary
        if (self.stats is None) | (self._ref!=ref):
            self._calculate_series_stats(ref=ref)
        
        return self.xg

    @property
    def ref():
        return self._ref
