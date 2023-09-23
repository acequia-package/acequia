"""
Module with GwCollection object holding a collection of groundwater 
head series.
"""

import warnings
from pandas import Series, DataFrame
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd

from .._read.gwfiles import GwFiles
from .._read.waterweb import WaterWeb
from .._read.hydromonitor import HydroMonitor

class GwCollection:
    """Collection of groundwater head series."""

    def __init__(self, gwcol):

        self._collection = gwcol
        self._stats = None
        self._xg = None
        self._ref = None

    def __len__(self):    
        return len(self._collection)

    def __repr__(self):
        return f'{self.__class__.__name__} (n={len(self)})'
    
    @classmethod
    def from_dinocsv(cls,filedir,loclist=None):
        """Create GwCollection object from folder with DinoLoket sourcefiles.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with Dinoloket csv sourcefiles.
        loclist : list, optional
            List of strings with valid location names to restrict
            number of files read from srcdir.
        """
        gwcol = GwFiles.from_dinocsv(filedir,loclist=loclist)
        return cls(gwcol)

    @classmethod
    def from_json(cls,filedir,loclist=None):
        """Create GwCollection object from folder with json sourcefiles.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with Dinoloket csv sourcefiles.
        loclist : list, optional
            List of strings with valid location names to restrict
            number of files read from srcdir.
        """
        gwcol = GwFiles.from_json(filedir,loclist=loclist)
        return cls(gwcol)

    @classmethod
    def from_waterweb(cls, filepath):
        """Create GwCollection object from WaterWeb csv export file.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with Dinoloket csv sourcefiles.

        Returns
        -------
        GwCollection object
        ...
        """
        wwn = WaterWeb.from_csv(fpath=filepath)
        return cls(wwn)

    @classmethod
    def from_hydromonitor(cls, filepath):
        """Create GwCollection object from Menyanthes hydromonitor csv export file.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with Dinoloket csv sourcefiles.

        Returns
        -------
        GwCollection object
        ...
        """
        hm = HydroMonitor(fpath=filepath)
        return cls(hm)


    def iteritems(self):
        """Iterate over all series in collecion and return gwseries 
        object."""
        for gw in self._collection.iteritems():
            yield gw


    def _calculate_series_stats(self,ref=None):
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

        self._stats = pd.concat(srstats_list,axis=1).T
        self._stats.index.name = 'series'
        self._xg = pd.concat(xg_list,axis=0)
        self._ref = ref


    def get_headstats(self,ref='datum'):
        """Return statistics of measured heads for each well filter."""
    
        # recalculate stats if nessesary
        if (self._stats is None) | (self._ref!=ref):
            self._calculate_series_stats(ref=ref)


        xcr = self._stats['xcr'].astype('float').values
        ycr = self._stats['ycr'].astype('float').values
        geometry = [Point(crd) for crd in zip(xcr,ycr)]
        points = gpd.GeoDataFrame(self._stats, geometry=geometry)
        points = points.set_crs('EPSG:28992')

        for colname in ['firstdate','lastdate',]:
            points[colname] = points[colname].apply(lambda x:x.strftime('%d-%m-%Y'))

        return points


    def get_xg(self,ref='datum'):
    
        # recalculate stats if nessesary
        if (self._stats is None) | (self._ref!=ref):
            self._calculate_series_stats(ref=ref)
        
        return self._xg


    def get_ecostats(self,ref='surface', units='days', step=5):
        """Return ecological most relevant statistics.

        Parameters
        ----------
        ref : {'datum','surface'}, default 'surface'
            Reference level for measurements.
        units : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int, default 5
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        pd.DataFrame
        ..."""

        ecostats = []
        for gw in self.iteritems():
            ecostats.append(gw.get_ecostats())
        return DataFrame(ecostats)

    def get_timestats(self, ref='datum', asgeo=True):

        statslist = []
        for gw in self.iteritems():

            # timestats table
            stats = gw.timestats(ref=ref)
            stats.name = gw.locname()
            stats = pd.DataFrame(stats).T
            locprops = gw.locprops()
            stats = pd.merge(stats,locprops,left_index=True,right_index=True, how='left')
            
            # order columns
            #firstcols = ['locname','filname']
            #colnames = firstcols + [col for col in stats.columns if col not in firstcols]

            statslist.append(stats.copy())
        stats = pd.concat(statslist)

        # create geodataframe
        if asgeo:
            xcr = stats['xcr'].astype('float').values
            ycr = stats['ycr'].astype('float').values
            geometry = [Point(crd) for crd in zip(xcr,ycr)]
            stats = gpd.GeoDataFrame(stats, geometry=geometry)
            stats = stats.set_crs('EPSG:28992')

        return stats

