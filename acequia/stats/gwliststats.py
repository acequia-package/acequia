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
    locs : list, optional
        list of location names
    gxg : bool, default False
        include GxG descriptive statistics

    Return
    ------
    pd.DataFrame

    """

    ds = aq.GwListStats(srcdir)
    tb = ds.srstats(gxg=gxg)

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
    pass


class GwListStats:
    """Return table of decriptive statistics for list of heads series

    Parameters
    ----------
    srcdir : str
        directory name with groundwater head source files
    locs : bool, default False
        aggegate results to locations

    """

    def __init__(self,srcdir=None,locs=None,gwlist=None,):

        self._gwlist = gwlist
        self._srcdir = srcdir
        self._locs = locs

        # Creating _gwlist might take a long time, it is created after 
        # calling _create_list()
        ##self._gwlist = None
        self._srstats = None

        if self._gwlist is None:

            if self._srcdir is None:
                raise ValueError((f'Name of  dino source directory must '
                    f'be given.'))

            if not os.path.isdir(self._srcdir):
                raise ValueError((f'{self._srcdir} is not a valid directory '
                    f'name.'))


    def __repr__(self):

        if not self._gwlist:
            mylen = 0
        else:
            mylen = len(self._gwlist)

        return (f'{self.__class__.__name__}(n={mylen})')



    def _create_list(self):
        """Create aq.GwList object"""
        self._gwlist = aq.GwList(srcdir=self._srcdir,loclist=self._locs)


    def srstats(self,ref='datum',gxg=False):
        """Return series statistics

        Parameters
        ----------
        ref : {'datum','surface','mp'}, default 'datum'
            head reference level
        gxg : bool, default False
            include GxG descriptive statistics
        """

        if self._gwlist is None:
            self._create_list()

        srstats_list = []
        xg_list = []
        for i,gw in enumerate(self._gwlist):

            if not gw._tubeprops.empty:
                desc = gw.describe(ref=ref,gxg=gxg)
                srstats_list.append(desc)
                xg_list.append(gw.xg(ref=ref,name=True))
            else:
                warnings.warn((f'{gw.name()} has no tubeproperties ' 
                    f' and will be ignored.'))

        self._srstats = pd.concat(srstats_list,axis=1).T
        self._srstats.index.name = 'series'

        self._xg = pd.concat(xg_list,axis=0)

        return self._srstats


    def xg(self):
        """Return xg3 statistics for all series"""

        if not hasattr(self,'_xg'):
            self.srstats()

        return self._xg



    def locstats(self):
        """Return location statistics"""


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


        if self._srstats is None:
            self._srstats = self.srstats()


        """
        missing_cols = [x for x in srstats.keys() 
            if x not in aggdict.keys()]
        if len(missing_cols)!=0:
            msg = f'Missing columns in aggdict :{missing_cols}'
            warnings.warn(msg)
        """

        tbloc = self._srstats.groupby(by=['locname']).agg(aggdict)
        tbloc.columns = tbloc.columns.get_level_values(0)
        tbloc = tbloc.drop('locname',axis=1)

        coldict = {'filname':'nfil','mean':'meandifcm'}
        tbloc = tbloc.rename(columns=coldict)

        return tbloc


    def save(self,fdir,ref='datum',gxg=False,prefix=None,suffix=None):
        """Save all tables to directory

        Parameters
        ----------
        fdir : str
            directory to save tables to 
        ref : {'datum', surface'}, default 'datum'
            reference level for heads
        prefix : str, optional
            prefix for filenames
        gxg : bool, default False
            include gxg statistics
        """
        if prefix is None:
            prefix = ''
 
        if not isinstance(prefix,str):
            warnings.warn((f'parameter prefix is of type {type(prefix)} ', 
                f'not type str. Prefix will be ignored.'))
            prefix = ''

        if suffix is None:
            suffix = ''
 
        if not isinstance(suffix,str):
            warnings.warn((f'parameter suffix is of type {type(suffix)} ', 
                f'not type str. Suffix will be ignored.'))
            suffix = ''

        if self._gwlist is None:
            self._create_list()

        if not self._gwlist.is_callable():
            self._create_list()

        # series statistics
        srstats = self.srstats(ref=ref,gxg=gxg)
        outfilepath = f'{fdir}{prefix}srstats{suffix}'
        srstats.to_csv(f'{outfilepath}.csv',index=True)
        srstats.to_excel(f'{outfilepath}.xlsx',index=True,merge_cells=False)

        # location statistics
        locstats = self.locstats()
        outfilepath = f'{fdir}{prefix}locstats{suffix}'
        locstats.to_csv(f'{outfilepath}.csv',index=True)
        locstats.to_excel(f'{outfilepath}.xlsx',index=True,merge_cells=False)

        # xg statistcs for each year
        if gxg==True:
            xg = self.xg()
            outfilepath = f'{fdir}{prefix}xg{suffix}'
            xg.to_csv(f'{outfilepath}.csv',index=True)
            xg.to_excel(f'{outfilepath}.xlsx',index=True,merge_cells=False)

