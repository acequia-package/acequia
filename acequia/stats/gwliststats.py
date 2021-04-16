"""Descriptive statistics of list of groundwater head series"""


import os
import warnings
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


def gwliststats(srcdir=None,ref=None,gxg=False):
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

    ds = aq.GwListStats(srcdir)
    tb = ds.timestatstable(gxg=gxg)

    return tb

def gwlocstats(srstats):
    """Return table of descriptive statistics for groundwater well 
    locations summarised from table of heads series statistics

    Parameters
    ----------
    srstats : pd.DataFrame
        table with series stats (as returned by  
        GwListTimeStats.timestatstable()

    Returns
    -------
    pd.DataFrame

    """

    def get_maxfrq(sr):
        """Return maximum observation frequency for a series"""
        frqs = ['daily','14days','month','seldom','never']

        if sr.empty:
            return None

        for freq in frqs:
            if np.any(sr==freq):
                return freq

    def get_maxdif(sr):
        """Calculate difference between maximum and minimum value
        in a series"""
        return np.round((sr.max()-sr.min())*100)


    aggdict = {
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
       'maxfrq':[get_maxfrq],
       'mean':[get_maxdif],
      }

    """
    missing_cols = [x for x in srstats.keys() 
        if x not in aggdict.keys()]
    if len(missing_cols)!=0:
        msg = f'Missing columns in aggdict :{missing_cols}'
        warnings.warn(msg)
    """

    tbloc = srstats.groupby(by=['locname']).agg(aggdict)
    tbloc.columns = tbloc.columns.get_level_values(0)
    #tbloc.columns = [col[0] for col in tbloc.columns]

    tbloc = tbloc.drop('locname',axis=1)

    coldict = {'filname':'nfil','mean':'meandifcm'}
    tbloc = tbloc.rename(columns=coldict)

    return tbloc


class GwListStats:
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

        # Creating _gwlist might take a long time, it is created after 
        # calling _create_list()
        self._gwlist = None

        if self.srcdir is None:
            raise ValueError((f'Name of  dino source directory must '
                f'be given.'))

        if not os.path.isdir(self.srcdir):
            raise ValueError((f'{self.srcdir} is not a valid directory '
                f'name.'))

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

        self.tbsr = pd.concat(srlist,axis=1).T
        self.tbsr.index.name = 'series'

        return self.tbsr

    def timestatstable(self,gxg=False):
        """Return table of decriptive statistics for list of heads series

        Parameters
        ----------
        locs : bool, default False
            aggregate descriptions of head series to locations
        gxg : bool, default False
            include GxG descriptive statistics
        """
        tb = self._table_series(gxg=gxg)
        return tb

