

import warnings
import numpy as np
from pandas import DataFrame,Series
import pandas as pd
import shapefile

import acequia as aq


def pointshape_write(tbl=None,xfield=None,yfield=None,filename='shapefile'):
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
    psw = aq.PointShapeWriter(tbl=tbl,xfield=xfield,yfield=yfield,filename=filename)


class PointShapeWriter:
    """Write dataset to shapefile"""

    def __init__(self,tbl=None,xfield=None,yfield=None,filename='shapefile'):
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
        self.filename = filename

        self.indexname = self.tbl.index.name
        self.colnames = [x for x in self.tbl.columns if x not in [self.xfield,self.yfield]]

        self.w = shapefile.Writer(self.filename, shapeType=1)
        self.w.field(self.indexname, 'C')


        # convert coordinates to numeric and delete rows with missing coords

        self.tbl[xfield] = pd.to_numeric(self.tbl[xfield])
        self.tbl[yfield] = pd.to_numeric(self.tbl[yfield])

        xmask = self.tbl[xfield].notnull().values
        ymask = self.tbl[yfield].notnull().values
        nmiss = len(self.tbl[~xmask | ~ymask])
        if nmiss!=0:
            msg = f'{nmiss} rows with missing coordinates were deleted.'
            warnings.warn(msg)
        self.tbl = self.tbl[xmask & ymask].copy()


        for name in self.colnames:
            self.w.field(name,'C')

        for idx,row in self.tbl.iterrows():

            self.w.point(row[self.xfield],row[self.yfield])

            reclist = [idx]
            for name in self.colnames:
                reclist.append(row[name])
            self.w.record(*reclist)

        self.w.balance()
        self.w.close()
