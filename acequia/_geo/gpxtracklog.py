
import os
from pandas import DataFrame, Series
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, shape

from .._read.gpxtree import GpxTree

class GpxTracklog:
    """Tracklog from GPS receiver as XML tree."""

    def __init__(self, gpxtree, filepath=None):
        """
        Parameters
        ----------
        gpxtree : GpxTree instance
            GPS tracklog data.
        filepath : str, optional
            Filepath to GPX tracklog file.
        """
        if not isinstance(gpxtree, GpxTree):
            raise ValueError((f"{type(gpxtree)} instance given instead of "
                f"<class 'GpxTree'> instance."))

        if filepath:
            if not os.path.exists(filepath):
                raise ValueError(f"Not a valid filepath: '{filepath}'.")

        self._gpxtree = gpxtree
        self._fpath = filepath

    @classmethod
    def from_file(cls,fpath):
        """Read gpx from file.
        
        Parameters
        ----------
        fpath : str
            Filepath to GPX tracklog file.

        Returns
        -------
        GPSTracklog instance
        """
        gpxtree = GpxTree.from_file(fpath)
        return cls(gpxtree=gpxtree,filepath=fpath);

    def _points_to_geodataframe(self,pointstable):
        """Return GeoDataFrame with points from Dataframe with lon and 
        lat columns.
        
        Parameters
        ----------
        pointstable : pandas DataFrame
            Table with lon and lat columns from GPX tree.
        """
        # lon = lengte (x), lat = breedte (y)
        lon = pointstable['lon'].astype('float').values
        lat = pointstable['lat'].astype('float').values
        geometry = [Point(crd) for crd in zip(lon,lat)]
        points = gpd.GeoDataFrame(pointstable, geometry=geometry)
        points = points.set_crs('EPSG:4326')
        return points

    def _get_track_date(self):
        """Return track recording date as str."""
        dates = self.trackpoints['time'].str.split('T').str[0]
        times = self.trackpoints['time'].str.split('T').str[1]
        
        if len(dates.unique())==1:
            return dates.unique()
        else:
            raise ValueError((f'Unexpected input: more than one date '
                f'found in trackpoints of {self._fpath}.'))

    @property
    def trackpoints(self):
        """Return trackpoints as GeoDataFrame"""
        trackpoints = self._gpxtree._get_trackpoints()
        if not trackpoints.empty:
            trackpoints = self._points_to_geodataframe(trackpoints)
        return trackpoints

    @property
    def tracks(self):
        """Return tracks as GeoDataframe"""
        points = self.trackpoints
        if points.empty:
            return points
        lines = points.groupby(['trackname','segmentid'])['geometry'].apply(
            lambda x: LineString(x.tolist()))
        lines = gpd.GeoDataFrame(lines, geometry='geometry')
        lines = lines.set_crs('EPSG:4326') # WGS84 longitude, latitude.       
        return lines

    @property
    def waypoints(self):
        """Return waypoints as GeoDataFrame."""
        pointstable = self._gpxtree.waypoints
        if pointstable.empty:
            return pointstable
        points = self._points_to_geodataframe(pointstable)
        return points

