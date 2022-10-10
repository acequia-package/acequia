"""
Read .gpx tracklog files created by GPS receivers. 
Supports GPX v1.0 and v1.1
"""

from pathlib import Path
from pandas import DataFrame, Series
import pandas as pd
from lxml import etree

class GpxTree:
    """XML tree with GPS receiver tracklog file."""

    def __init__(self,tree, filepath=None):
        """
        Parameters
        ----------
        tree : ElementTree
            XML tree with data from .gpx file.
        flepath : str
            Filepath to .gpx sourcefile, optional
        """
        self._tree = tree
        self._filepath = filepath

        try:
            self._root = self._tree.getroot()
            self._ns = self._root.nsmap
        except AttributeError as err:
            clsname = tree.__class__.__name__
            raise AttributeError((f'Invalid gpx tree of class {clsname}'))

        # dict of nodes under root
        self._nodes_under_root = {}
        for node in self._root.iterchildren():            
            tag = node.tag
            key = tag.split('}')[1] # drop namespace
            self._nodes_under_root[key] = node

    def __repr__(self):
        try:
            return f"{self.__class__.__name__} ('{self.meta['desc']}')"
        except KeyError as err:
            return f"{self.__class__.__name__} ()"

    @classmethod
    def from_file(cls,fpath):
        """Read gpx from file.
        
        Parameters
        ----------
        fpath : str
            Valid filepath to .gpx file.

        Returns
        -------
        GpxTree
        """
        try:
            open(Path(fpath)) #test open to get usefull error message
            tree = etree.parse(fpath)
            
        except FileNotFoundError as error:
            raise FileNotFoundError(error) from None
        except OSError as error:
            raise OSError(error) from None

        return cls(tree,filepath=fpath)

    def _get_meta(self):
        """Extract tracklog metadata."""
        
        # metadata from root node
        self._meta = {}
        try:
            self._meta['gpx_version'] = self._root.attrib['version']
            self._meta['creator'] = self._root.attrib['creator']
        except (AttributeError,KeyError) as err:
            self._meta['gpx_version'] = None
            self._meta['creator'] = None
            print(err)

        # metadata from root child nodes
        if 'metadata' in self._nodes_under_root.keys(): #GPX v1.1
            node = self._nodes_under_root['metadata']
            for child in node:
                key = child.tag.split('}')[1] #drop namespace
                value = child.text
                if not value is None:
                    self._meta[key] = value
        else: #GPX v1.0
            for key in ['name','desc','time','keywords']:
                if key in self._nodes_under_root.keys():
                    value = self._nodes_under_root[key].text
                    if value is not None:
                        self._meta[key] = value
        return self._meta

    def _get_waypoints(self):
        """Extract waypoints from xml tree."""

        # extract waypoints from tree
        waypoints = []
        for wpnode in self._root.findall(f'.//wpt',self._ns):
            wp = {}
            wp['lat'] = wpnode.attrib['lat']
            wp['lon'] = wpnode.attrib['lon']
            for child in wpnode.iterchildren():
                key = child.tag.split('}')[1] #drop namespace
                wp[key] = child.text
            waypoints.append(wp)

        return DataFrame(waypoints)


    def _get_trackpoints(self):
        """Extract trackpoints from xml tree."""

        # iterate over track nodes
        trackpoints = []
        for tracknode in self._root.findall(f'.//trk',self._ns):
            trackname = tracknode.find(f'.//name',self._ns).text

            # iterate over track segments
            for tracksegment in tracknode.findall(f'.//trkseg',self._ns):
                segmentid = 0

                # iterate over segment trackpoints 
                for trackpoint in tracksegment.iterchildren():
                    tp = {}
                    tp['trackname'] = trackname
                    tp['segmentid'] = str(segmentid)
                    
                    # attribute of trackpoint
                    tp['lat'] = trackpoint.attrib['lat']
                    tp['lon'] = trackpoint.attrib['lon']
                    
                    # children of trackpoint
                    for child in trackpoint.iterchildren():
                        key = child.tag.split('}')[1] #drop namespace
                        tp[key] = child.text

                    trackpoints.append(tp)

                segmentid+=1

        return DataFrame(trackpoints)

    @property
    def meta(self):
        """Return .gpx metadata as DataFrame."""
        return self._get_meta()

    @property
    def bounds(self):
        """Return boundary of tracklog as Dict."""
        bounds_node = self._root.find(f'.//bounds',self._ns)
        try:
            return bounds_node.attrib
        except AttributeError as err:
            return {'minlat':None, 'minlon':None, 'maxlat':None,'maxlon':None}
        return ''

    @property
    def trackpoints(self):
        """Return .gpx trackpoints as DataFrame."""
        return self._get_trackpoints()

    @property
    def waypoints(self):
        """Return .gpx waypoints as DataFrame."""
        data = self._get_waypoints()
        return data

    @property
    def contents(self):
        """Return names of tags below xml root as list."""
        return list(self._nodes_under_root.keys())
