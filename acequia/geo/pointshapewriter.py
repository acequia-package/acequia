

import warnings
import numpy as np
from pandas import DataFrame,Series
import pandas as pd
from shapely.geometry import Point
from geopandas import GeoDataFrame



def pointshape_write(tbl=None,xfield=None,yfield=None,
    filepath='shapefile.shp'):
    """Write pandas dataframe to point shapefile

    Parameters
    ----------
    tbl : pd.DataFrame
        table with data
    xfield : str
        column name with xcoordinates
    yfield : str
        column name with ycoordinates
    filename : str
        shapefile name

    """
    psw = PointShapeWriter(tbl=tbl,xfield=xfield,yfield=yfield,
        filepath=filepath)


class PointShapeWriter:
    """Write dataset to shapefile

    Methods
    -------
    
    """

    def __init__(self,tbl=None,xfield=None,yfield=None,
        filepath='shapefile,shp'):
        """Write pandas dataframe to point shapefile

        Parameters
        ----------
        tbl : pd.DataFrame
            table with data
        xfield : str
            column name with xcoordinates
        yfield : str
            column name with ycoordinates
        filename : str
            shapefile name

        """
        self.tbl = tbl.copy()
        self.xfield = xfield
        self.yfield = yfield
        self.filepath = filepath

        self.indexname = self.tbl.index.name
        #self.colnames = [x for x in self.tbl.columns 
        #    if x not in [self.xfield,self.yfield]]
        self.colnames = self.tbl.columns

        self._remove_missing_crd()
        self._create_shapefile()
        #self.write()

    @classmethod
    def writefile(cls,tbl=None,xfield=None,yfield=None,
        filepath='shapefile,shp'):

        shapewriter = cls.__init__(cls,tbl=tbl,xfield=xfield,
        yfield=yfield,filepath=filepath)
        shapewriter.write()
        return shapewriter


    def _remove_missing_crd(self):

        # convert coordinates to numeric and delete rows with missing coords
        self.tbl[self.xfield] = pd.to_numeric(self.tbl[self.xfield])
        self.tbl[self.yfield] = pd.to_numeric(self.tbl[self.yfield])

        # remove points with missing coordinates
        xmask = self.tbl[self.xfield].notnull().values
        ymask = self.tbl[self.yfield].notnull().values
        nmiss = len(self.tbl[~xmask | ~ymask])
        self.tbl = self.tbl[xmask & ymask].copy()

        # show warning
        if nmiss!=0:
            msg = f'{nmiss} rows with missing coordinates were deleted.'
            warnings.warn(msg)


    def _create_shapefile(self):

        wp = self.tbl
        geometry = [Point(xy) for xy in zip(wp['xcr'],wp['ycr'])]
        self.gdf = GeoDataFrame(wp, geometry=geometry)
        self.gdf = self.gdf.set_crs('epsg:7415')

        for colname in self.gdf.columns:
            if colname not in ['geometry']:
                self.gdf[colname] = self.gdf[colname].astype(str)


    def write(self):

        """
        # create scheme with all cols as str
        propdict = {}
        propdict[self.gdf.index.name] = 'str'
        for colname in self.gdf.columns:
            propdict[colname] = 'str'
        propdict.pop('geometry', None)

        schema = {
            'geometry': 'Point',
            'properties': propdict
            }
        """

        # write shapefile
        self.gdf.to_file(self.filepath) #,schema=schema)
