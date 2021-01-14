"""Descriptive statistics of list of groundwater head series"""


import os
import warnings
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


def timestatstable(srcdir=None,ref=None,locs=None,gxg=False):
    """Return table of decriptive statistics for multiple heads series

    Parameters
    ----------
    srcdir : str
        directory name with groundwater head source files
    ref : {'datum','surface','mp'}, default 'datum'
        head reference level
    srctype : str, optional
        sourcefile type (will be inferred if not given)
    locs : bool, default False
        aggegate results to locations
    gxg : bool, default False
        include GxG descriptive statistics

    Return
    ------
    pd.DataFrame

    """

    ds = aq.DescribeGwList(srcdir)
    tb = ds.timestatstable(locs=locs, gxg=gxg)

    return tb


class DescribeGwList:
    """Return table of decriptive statistics for list of heads series

    Parameters
    ----------
    srcdir : str
        directory name with groundwater head source files
    ref : {'datum','surface','mp'}, default 'datum'
        head reference level
    srctype : str, optional
        sourcefile type (will be inferred if not given)
    locs : bool, default False
        aggegate results to locations

    """


    def __init__(self,srcdir=None,ref=None,srctype=None,locs=None):

        self.srcdir = srcdir
        self.ref = ref
        self.srctype = srctype
        self.locs = locs
        

        # Creating _gwlist might take a long time, it is created after calling
        # _create_list()
        self._gwlist = None

        if self.srcdir is None:
            raise ValueError(f'Name of  dino source directory must be given.')

        if not os.path.isdir(self.srcdir):
            raise ValueError(f'{self.srcdir} is not a valid directory name.')

        #if self.ref is None:
        #    self.ref = 'datum'

        #if self.ref not in aq.GwSeries._reflevels:
        #    msg = f'{self.ref} is not a valid reference level name'
        #    raise ValueError(msg)


    def __repr__(self):

        if not self._gwlist:
            mylen = 0
        else:
            mylen = len(self._gwlist)

        return (f'{self.__class__.__name__}(n={mylen})')


    def _create_list(self):
        """Create aq.GwList object"""
        self._gwlist = aq.GwList(srcdir=self.srcdir) #, srctype=self.srctype)


    def _table_series(self,gxg=False):
        """Create table of series statistics

        Parameters
        ----------
        gxg : bool, default False
            include GxG descriptive statistics
        """

        if self._gwlist is None:
            self._create_list()

        for i,gw in enumerate(self._gwlist):

            if i==0:
                srlist = []

            if not gw._tubeprops.empty:
                desc = gw.describe(ref=self.ref,gxg=gxg)
                srlist.append(desc)

        self.tbsr = pd.concat(srlist)
        self.tbsr.index.name = 'series'

        return self.tbsr


    def _table_locs(self):
        """Return table of location statistics"""

        if self._gwlist is None:
            self._table_series()

        self._aggdict = {
           'locname':'first',
           'filname':'size',
           'alias':'first',
           'surfacelevel':'first',
           'filbot':'min',
           'xcr':'first',
           'ycr':'first',
           'firstdate':'min',
           'lastdate':'max',
           'minyear':'min',
           'maxyear':'max',
           'nyears':'max',
           'yearspan':'max',
          } #todo: add difference of mean head between filters

        self._missing_cols = [x for x in self.tbsr.keys() if x not in self._aggdict.keys()]
        if self._missing_cols:
            msg = f'Missing columns in aggdict :{self._missing_cols}'
            #warnings.warn(msg)

        self.tbloc = self.tbsr.groupby(by=['locname']).agg(self._aggdict)
        coldict = {'filname':'nfil','filbot':'filbot_first',}
        self.tbloc = self.tbloc.rename(columns=coldict)

        return self.tbloc


    def timestatstable(self,locs=None, gxg=False):
        """Return table of decriptive statistics for list of heads series

        Parameters
        ----------
        locs : bool, default False
            aggregate descriptions of head series to locations
        gxg : bool, default False
            include GxG descriptive statistics
        """

        if not locs:
            tb = self._table_series(gxg=gxg)
        else:
            tb = self._table_locs()

        return tb

