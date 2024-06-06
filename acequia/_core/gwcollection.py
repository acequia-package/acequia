"""
Module with GwCollection object holding a collection of groundwater 
head series.
"""

import os
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import geopandas as gpd

from .._core.gwseries import GwSeries
from .._read.gwfiles import GwFiles
from .._read.waterweb import WaterWeb
from .._read.hydromonitor import HydroMonitor
from .._read.brogwcollection import BroGwCollection
from .._plots.plotheads import PlotHeads

class GwCollection:
    """Collection of groundwater head series."""

    """Collection sources should have the following methods:
    len(), iteritems(), get_series() 
    and the following properties:
    names, loclist
    """


    STATS_REFLEVEL = GwSeries.REFLEVEL_DEFAULT

    def __init__(self, gwcol):

        self._collection = gwcol
        self._tubestats = DataFrame()
        self._xg = DataFrame()
        #self._statsref = None

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

    @classmethod
    def from_brodownload(cls, xmin=None, xmax=None, ymin=None, ymax=None,
        title=None):
        """Download data from BRO website.

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
            
        """
        bro = BroGwCollection.from_rectangle(
            xmin=xmin, 
            xmax=xmax, 
            ymin=ymin, 
            ymax=ymax,
            title=title)
        return cls(bro)

    @property
    def names(self):
        """Return list of series names."""
        return self._collection.names


    def get_gwseries(self, series):
        """Return GwSeries object.
        
        Parameters
        ----------
        series : str
            Valid name for series in collection.
            
        Returns
        -------
        GwSeries
            
        """
        gw = self._collection.get_gwseries(series)
        return gw


    def iteritems(self):
        """Iterate over all series in collecion and return gwseries 
        object."""
        for gw in self._collection.iteritems():
            yield gw


    """
    def _calculate_series_stats(self, ref=None, gxg=False):
        # Calculate statistics for all series and set internal variables.

        Parameters
        ----------
        ref : {'datum','surface','mp'}, default 'datum'
            head reference level
        
        self.STATS_REFLEVEL = ref
        srstats_list = []
        xg_list = []
        for gw in self.iteritems():

            if len(gw)==0: # empty gwseries
                continue

            if gw.tubeprops().empty:
                #warnings.warn((f'{gw.name()} has no tubeproperties ' 
                #    f' and will be ignored.'))
                continue

            if not gxg:
                desc = gw.describe(ref=ref, gxg=False)
            else:
                desc = gw.describe(ref=ref, gxg=True)
                xg_list.append(gw.xg(ref=ref, name=True))
            srstats_list.append(desc)

        self._stats = pd.concat(srstats_list, axis=1).T
        self._stats.index.name = 'series'
        if not gxg:
            self._xg = None
        else:
            self._xg = pd.concat(xg_list, axis=0)
    """


    def get_tubestats(self, ref='datum', minimal=True, geom=True):
        """Return selection of properties and descriptive statistics.

        Parameters
        ----------
        ref  : {'mp','datum','surface'}, default 'datum'
            choosen reference level for groundwater heads
        minimal : bool, default True
            return minimal selection of statistics
        geom : bool, default True
            Return GeoDataFrame.

        Returns
        -------
        pd.DataFrame
            
        """
        
        # return previously calculated statistics, if present
        if (not self._tubestats.empty) & (self.STATS_REFLEVEL==ref) & (minimal==minimal):
            return self._tubestats

        # calculate tubestats for all series
        statslist = []
        for gw in self.iteritems():

            if len(gw)==0: # empty gwseries
                continue

            stats = gw.describe(ref=ref, gxg=False, minimal=minimal)
            statslist.append(stats)

        tubestats = pd.concat(statslist, axis=1).T

        # convert date columns to string columns
        for colname in ['firstdate','lastdate',]:
            tubestats[colname] = tubestats[colname].apply(
                lambda x:x.strftime('%d-%m-%Y') if not pd.isnull(x) else np.nan)

        if geom:
            tubestats = self._statstable_to_geodataframe(tubestats)

        return tubestats


    def _statstable_to_geodataframe(self, stats):
        """Calculate geometry from Pandas DataFrame with statistics and
        return Geopandas geodataframe.

        Parameters
        ----------
        stats : DataFrame
            Table with statistics and fields xcr and ycr

        Returns
        -------
        GeoDataFrame

        Notes
        -----
        Assumes coordinates are stored in fiels xcr and ycr
        and crs is EPSG:28992.
            
        """ 
        xcr = stats['xcr'].astype('float').values
        ycr = stats['ycr'].astype('float').values
        geometry = [Point(crd) for crd in zip(xcr, ycr)]
        points = gpd.GeoDataFrame(stats, geometry=geometry)
        points = points.set_crs('EPSG:28992')
        return points


    """
    def get_headstats(self,ref='datum'):
        #Return statistics of measured heads for each well filter.

        # recalculate stats if nessesary
        if (self._stats is None) | (self.STATS_REFLEVEL!=ref):
            self._calculate_series_stats(ref=ref)

        points = self._statstable_to_geodataframe(stats)
        for colname in ['firstdate','lastdate',]:
            points[colname] = points[colname].apply(lambda x:x.strftime('%d-%m-%Y'))

        return points
    """

    def get_gxg(self, ref='datum', minimal=True):
    
        # calculate xg for all series
        self.STATS_REFLEVEL = ref
        gxg_list = []
        for gw in self.iteritems():

            if len(gw)==0: # empty gwseries
                continue

            if gw.tubeprops().empty: # no tubeprops available
                continue #todo: return empty dataframe with columns

            gxg = gw.gxg(ref=ref, minimal=minimal)
            #gxg_list.append(gw.xg(ref=ref, name=True))
            gxg_list.append(gxg)
        gxg = pd.concat(gxg_list, axis=1).T

        # todo: merge fith filterstats
        return gxg


    def get_ecostats(self,ref='surface', units='days', step=5, geom=True):
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
        geom : bool, default True
            Return GeoDataFrame.

        Returns
        -------
        pd.DataFrame, gpd.GeoDataFrame
           """

        stats_list = []
        crd_list = []
        for gw in self.iteritems():

            if len(gw)==0:
                continue

            stats_list.append(gw.get_ecostats())
            if geom:
                crd_list.append({
                    'series' : gw.name(),
                    'xcr' : gw.locprops().loc[gw.locname(),'xcr'],
                    'ycr' : gw.locprops().loc[gw.locname(),'ycr'],
                    })

        ecostats = DataFrame(stats_list)

        # create geodataframe
        if geom:
            crd = DataFrame(crd_list).set_index('series')
            ecostats = pd.merge(ecostats, crd, left_index=True, right_index=True, how='left')
            ecostats = self._statstable_to_geodataframe(ecostats)
            """
            xcr = crd['xcr'].astype('float').values
            ycr = crd['ycr'].astype('float').values
            geometry = [Point(crd) for crd in zip(xcr,ycr)]
            ecostats = gpd.GeoDataFrame(ecostats, geometry=geometry)
            ecostats = ecostats.set_crs('EPSG:28992')
            """

        return ecostats

    """
    def get_timestats(self, ref='datum', geom=True):

        statslist = []
        for gw in self.iteritems():

            # empty gwseries
            if len(gw)==0:
                continue

            # timestats table
            stats = gw.timestats(ref=ref)
            #stats.name = gw.locname()
            stats.name = gw.name()
            stats = pd.DataFrame(stats).T
            locprops = gw.locprops()
            stats = pd.merge(stats,locprops,left_index=True,right_index=True, how='left')
            
            # order columns
            #firstcols = ['locname','filname']
            #colnames = firstcols + [col for col in stats.columns if col not in firstcols]

            statslist.append(stats.copy())
        stats = pd.concat(statslist)

        # create geodataframe
        if geom:
            xcr = stats['xcr'].astype('float').values
            ycr = stats['ycr'].astype('float').values
            geometry = [Point(crd) for crd in zip(xcr,ycr)]
            stats = gpd.GeoDataFrame(stats, geometry=geometry)
            stats = stats.set_crs('EPSG:28992')

        return stats
    """
    def to_json(self, path):
        """Write äll series to json files.
        
        Parameters
        ----------
        path : str
            Valid path to output directory.
        
        """
        if not os.path.isdir(path):
            raise ValueError(('Not a valid direcotry path: {path}'))

        for gwname in self._collection.names:
            gw = self._collection.get_gwseries(gwname)
            gw.to_json(path);


    def plot_heads(self, ref='datum', bylocation=True, dirpath=None, dpi=200):
        """Plot heads for all locations.
        
        Parameters
        ----------
        ref : {'datum','surface','mp'}, default 'datum'
            Reference level for groundwater heads.

        bylocation : bool, default True
            Plot all series for a single well in one graph.

        dirpath : str, optional
            Path to graph output directory.

        dpi : float|int, default 200
            Output file resolution.
           
        Notes
        -----
        If no output directory is given, series are plotted to screen.
            
        """
        if ref not in GwSeries.REFLEVELS:
            raise ValueError((f'Invalid reference level "{ref}". '
                f'(Valid reference levels are "{GwSeries.REFLEVELS}".'))

        if dirpath:
            if not os.path.isdir(dirpath):
                raise ValueError((f'Not a valid output directory: {dirpath}.'))

        if not bylocation: # plot each series on seperate graph
            for srname in self._collection.names:
                gw = self._collection.get_gwseries(srname)
                if gw.heads().empty:
                    warnings.warn((f'Empty series {gw.name()} was not plotted.'))
                    continue

                if dirpath: # plot to file
                    plot = PlotHeads(gw, ref=ref);
                    plot.save(f'{dirpath}{gw.name()}.jpg', dpi=dpi)
                    plt.close(plot._fig)
                else: # plot to screen
                    PlotHeads(gw, ref=ref)
                    plt.show()
                    plt.close()
           
        else: # plot all series for location in one graph

            for loclist in self._collection.loclist: # return list of list

                gwlist = []
                for srname in loclist:
                    gw = self._collection.get_gwseries(srname)
                    #if not gw.heads().empty:
                    gwlist.append(gw)

                if dirpath: # plot to file
                    plot = PlotHeads(gwlist, ref=ref);
                    locname = gwlist[0].gw.locname()
                    plot.save(f'{dirpath}{locname}.jpg', dpi=dpi)
                    plt.close(plot._fig)
                else: # plot to screen
                    PlotHeads(gwlist, ref=ref)
                    plt.show()
                    plt.close()

        
        
        
        