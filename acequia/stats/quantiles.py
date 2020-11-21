""" This module contains a class Quantiles that calculates quantiles
of measured heads for hydrological years.

Author: Thomas de Meij

"""

from datetime import datetime
import datetime as dt
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
import matplotlib.pyplot as plt

import acequia as aq


class Quantiles:
    """Calculate quantiles from series of measured heads"""

    n14 = 18

    def __init__(self, ts=gw, srname=None, ref='surface', nclasses=10):
        """
        Parameters
        ----------
        ts : pd.Series, aq.GwSeries
            timeseries with groundwater head measurments

        ref : str, ['datum','surface']
            reference level for measurements

        nclasses : int (default 10)
            number of quantile classes 

        """

        if isinstance(gw,aq.GwSeries):
            ts = gw.heads(ref=ref)
            if srname is None:
                srname = gw.name()

        if isinstance(gw,pd.Series):
            ts = gw
            if srname is None: 
                srname = ts.name

        if srname is None: 
            srname = 'series'

        self.gw = gw
        self.ref = ref
        self.ts = ts
        self.srname = srname

        # calculate quantiles table
        self.qt = np.linspace(0,1,nclasses+1) # list of quantiles
        self.qtnames = ['p'+str(int(x*100)) for x in self.qt]
        self.tbl = self._quantiles()


    def _quantiles(self):
        """Return table with quantiles for each hydrological year"""

        # empty table with hydroyears and percentiles
        hydroyear = aq.hydroyear(self.ts)
        #allyears = np.arange(hydroyear.min(),hydroyear.max()+1)
        tbl = pd.DataFrame(index=set(hydroyear),columns=self.qtnames)

        for i,(name,val) in enumerate(zip(self.qtnames,self.qt)):
            grp = self.ts.groupby(hydroyear)
            tbl[name] = grp.quantile(val)

        return tbl


    def table(self):
        """Return table of quantiles for each hydrological year"""
        return self.tbl


    def plot(self,years=None,figname=None, figtitle=None):
        """Plot quantiles"""

        if years is None:
            years = []

        if not isinstance(years,list):
            msg = f'years of type {type(list)} changed to empty list'
            warnings.warn(msg)
            years = []

        if figtitle is None:
            figtitle = self.srname

        csurf = '#8ec7ff'
        clines = '#c1e0ff'
        cyears = '#b21564'

        fig,ax = plt.subplots(1,1)
        fig.set_figwidth(13)
        fig.set_figheight(7)

        tbl = self.tbl
        x = self.qt
        upper = [tbl[col].quantile(0.05)*100 for col in tbl.columns]
        lower = [tbl[col].quantile(0.95)*100 for col in tbl.columns]
        ax.fill_between(x, upper, lower, color=csurf) 

        for year in self.tbl.index:

            yvals = self.tbl.loc[year,:].values * 100
            xvals = self.qt
            ax.plot(xvals,yvals,color=clines)

        for year in years:
            yvals = self.tbl.loc[year,:].values * 100
            xvals = self.qt
            ax.plot(xvals,yvals,color=cyears)

        ax.set_xticks(self.qt)
        ax.set_xticklabels(self.qtnames)

        ax.set_xlim(1,0)
        #ax.set_ylim(0,375)

        ax.invert_xaxis()
        if self.ref=='surface':
            ax.invert_yaxis()

        #fig.suptitle('test title', fontsize=12)
        ax.set_xlabel('percentiel', fontsize=15)
        ax.set_ylabel('grondwaterstand', fontsize=15)


        ax.text(0.99, 0.97, figtitle, horizontalalignment='right',
                verticalalignment='top', transform=ax.transAxes,
                fontsize = 16)

        if figname is not None:
            plt.savefig(figname,bbox_inches='tight')

        plt.show()
        return ax
