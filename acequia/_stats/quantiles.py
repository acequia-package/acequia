""" This module contains a class Quantiles that calculates quantiles
of measured heads for hydrological years.

"""

from datetime import datetime
import datetime as dt
import math
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd
import matplotlib.pyplot as plt

from .._core.gwseries import GwSeries
from .utils import hydroyear

class Quantiles:
    """Calculate cumulative frequencies of groundwater head series."""

    N14 = 18

    def __init__(self, heads, srname=None, headsref='surface'):
        """
        Calculate quantiles from series of measured heads.

        Parameters
        ----------
        heads : pd.Series, aq.GwSeries
            Timeseries with groundwater head measurements.

        srname : str
            User defined series name.

        headsref : {'datum','surface'}, default 'surface'
            Reference level for measurements.

        """

        if isinstance(heads,GwSeries):
            ts = heads.heads(ref=headsref)
            if srname is None:
                srname = heads.name()

        elif isinstance(heads,pd.Series):
            ts = heads
            if srname is None: 
                srname = heads.name
                
        elif isinstance(heads,DataFrame):
            ts = heads.iloc[:,0].squeeze()
            if srname is None: 
                srname = list(heads)[0]

        self._heads = heads
        self.headsref = headsref
        self.ts = ts
        self.srname = srname


    def __repr__(self):
        return f'{self.__class__.__name__}({self.srname})'


    def get_quantiles(self, unit='days', step=None):
        """Return table with quantiles for each hydrological year.
        
        Parameters
        ----------
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        DataFrame, table with cumulative frequencies.
        """

        # set values for cumulative frequency table
        if unit=='days':
            if step is None: 
                step = 30
            if not 0 < step < 366:
                warnings.warn((f'For unit days, step must be an '
                    f'integer between 0 and 366, not {step}. '
                    f'Default value of 30 will be used.'))
                step = 30
            self.days = list(range(0,366,step))
            self.qt = [x/365 for x in self.days]
            self.qtlabels = [str(x) for x in self.days]

        elif unit=='quantiles':
            if step is None: 
                step = 0.1
            if not 0 < step < 1:
                warnings.warn((f'For unit quantiles, step must be a '
                    f'fraction between 0 and 1, not {step}. '
                    f'Default value of 0.1 will be used.'))
                step = 0.1

            self.qt = np.arange(0,1+step,step) # list of quantiles
            self.qt = self.qt[self.qt<=1] #delete qts >1.0
            self.qtlabels = ['p'+str(int(x*100)) for x in self.qt]
            self.days = [int(x*365) for x in self.qt]

        else:
            raise ValueError((f'Value for parameter unit must be "days" '
                f'or "quantiles", not {unit}'))

        # create empty table with hydroyears and percentiles
        hydroyears = hydroyear(self.ts)
        unique_years = np.unique(hydroyears)
        quantiles = pd.DataFrame(index=unique_years,columns=self.qtlabels)

        # calculate quantiles
        grp = self.ts.groupby(hydroyears)
        for i,(name,quantile) in enumerate(zip(self.qtlabels,self.qt)):
            if self.headsref=='datum':
                quantiles[name] = grp.quantile(quantile).round(2)
            elif self.headsref=='surface':
                quantiles[name] = grp.quantile(quantile)*100
                quantiles[name] = quantiles[name].apply(
                    lambda x:math.floor(x) if not np.isnan(x) else x)
                ##).round(0).astype(int)
        return quantiles

    def get_summary(self,unit='days',step=None, decimals=2):
        """Return table with summary of quantile statistics.
        
        Parameters
        ----------
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.
        decimals : int, default 2
            Round results to specified number of decimals.

        Returns
        -------
        DataFrame
        """
        qt = self.get_quantiles(unit=unit,step=step)

        decimals = 2
        q05 = qt.quantile(q=0.05, axis=0, numeric_only=True).round(decimals)
        q95 = qt.quantile(q=0.95, axis=0, numeric_only=True).round(decimals)
        mean = qt.mean().round(decimals)
        std = qt.std().round(decimals)
        count = qt.count()

        summary = pd.concat({'q05':q05,'q95':q95,'mean':mean,'std':std,'count':count},axis=1).T
        if self.headsref == 'surface': # round all values to zero decimals
            rows = []
            for rowlabel in summary.index:
                rows.append(summary.loc[rowlabel,:].apply(
                    lambda x:math.floor(x) if not np.isnan(x) else x))
            summary = DataFrame(rows)
            
        return summary

    def get_inundation(self, unit='days', step=5):
        """Return number of days with inundation as mean, min, max.
        
        Parameters
        ----------
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int, default 5
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        pandas.Series
        ...
        """

        def get_negative_days(sr):
            if sr[sr<0].empty:
                return 0
            return float(sr[sr<0].index[-1])

        summary = self.get_summary(unit=unit,step=step)
        sr = Series(data=[
            get_negative_days(summary.loc['mean',:]),
            get_negative_days(summary.loc['q95',:]),
            get_negative_days(summary.loc['q05',:]),
            ],index = ['mean','min','max'],name='inundationtime')

        if self.headsref == 'surface': # round all values to zero decimals
            sr = sr.apply(lambda x:math.floor(x) if not np.isnan(x) else x)

        return sr

    def get_lowest(self, unit='days', step=5):
        """Return lowest measured heads.
        
        Parameters
        ----------
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int, default 5
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.

        Returns
        -------
        pandas.Series
        """

        summary = self.get_summary(unit=unit,step=step)
        lastcol = summary.columns[-1]
        sr = Series([
            summary.at['mean',lastcol],
            summary.at['q05',lastcol],
            summary.at['q95',lastcol],
            ], index = ['mean','min','max'],
            name='lowest')
        return sr



    def plot(self, unit='days', step=30, median=False, coloryears=None, 
        boundyears=None, figpath=None, figtitle=None, ylim=None, ax=None):
        """Plot quantiles

        Parameters
        ----------
        unit : {'days','quantiles'}, default 'days'
            Unit of quantile boundary classes.
        step : float or int,default 30
            Quantile class division steps. For unit days an integer 
            between 0 and 366, for unit quantiles a fraction between 
            0 and 1.
        median : bool, default False
            ...
        coloryears : list of int, optional
            List of years to plot in color
        boundyears : list, optional
            List of years to include in calculating boundaries for 
            filled surface.
        figpath : str, optional
            figure output path
        figtitle : str, optional
            figure title
        ylim : list, optional
            [yaxmin, yaxmax]
        ax : matplotlib.axes.Subplot, optional
            Ax to plot on.

        Returns
        -------
        matplotlib.pyplot.ax
           
        """

        quantiles = self.get_quantiles(unit=unit, step=step)

        if coloryears is None:
            coloryears = []

        if not isinstance(coloryears,list):
            warnings.warn((f'years of type {type(colorlist)} changed to ' 
                'empty list'))
            years = []

        if figtitle is None:
            figtitle = self.srname

        csurf = '#8ec7ff'
        clines = '#2f90f1' #'#979797' #
        cyears = '#b21564'
        cmedian = '#8b0000'

        if ax is None:
            fig,ax = plt.subplots(1,1)
            fig.set_figwidth(8)
            fig.set_figheight(4)

        x = self.qt
        reftbl = quantiles.copy()
        if boundyears is not None:
            idx = [x for x in reftbl.index.values if x not in boundyears]
            reftbl = reftbl.loc[idx,:]

        # reference based on quantiles
        upper = reftbl.quantile(0.05) #*100
        lower = reftbl.quantile(0.95) #*100

        # alternative reference
        #mean = reftbl.median(axis=0,skipna=True)
        #std = reftbl.std(axis=0,skipna=True)
        #upper = (mean+std)*100
        #lower = (mean-std)*100

        # alternative reference 2
        # leave out lowest line
        #upper = [reftbl[col].sort_values()[:-1].quantile(0.05)*100 for col in reftbl.columns]
        #lower = [reftbl[col].sort_values()[:-1].quantile(0.95)*100 for col in reftbl.columns]

        # draw colored surface with reference
        ax.fill_between(x, upper, lower, color=csurf, alpha=0.5) 
        
        # plot line for each year
        for year in quantiles.index:
            yvals = quantiles.loc[year,:].values #* 100
            xvals = self.qt
            ax.plot(xvals, yvals, color=clines)

        # plot colored lines
        for year in quantiles.index:
            if year in coloryears:
                yvals = quantiles.loc[year,:].values #* 100
                xvals = self.qt
                ax.plot(xvals,yvals,color=cyears)

        if median:
            yvals = quantiles.median().values #* 100
            xvals = self.qt
            ax.plot(xvals,yvals,color=cmedian)

        # plot horizontal line
        xmin, xmax = ax.get_xlim()
        ax.hlines(0, xmin, xmax, colors='#808080', linestyles='solid')

        # xax set ticks
        qtlen = len(self.qt)
        step = int(np.ceil((qtlen-2)/6))
        idx = list(range(0,qtlen,step))
        xticks = [self.qt[i] for i in idx]
        ax.set_xticks(xticks)

        #qlabels = list(quantiles)
        #qlables = ['0','90','180','270','360']
        qtlabels = [self.qtlabels[i] for i in idx]
        ax.set_xticklabels(qtlabels,fontsize=7.) ##self.qtlabels)
        if unit=='days':
            ax.set_xlabel('dagen/jaar') #, fontsize=15)
        else:
            ax.set_xlabel('percentiel') #, fontsize=15)
        ax.set_xlabel('')

        ax.set_xlim(1,0)
        ax.invert_xaxis()

        # format yax
        if self.headsref=='surface':
            ax.invert_yaxis()

        if ylim is not None:
            ax.set_ylim(ylim[0],ylim[1])

        yticklabels = [str(int(x)) for x in ax.get_yticks()]
        ax.set_yticklabels(yticklabels,fontsize=10.) 
        
        ax.set_ylabel('')

        ax.text(0.99, 0.97, figtitle, horizontalalignment='right',
                verticalalignment='top', transform=ax.transAxes,
                fontsize = 10.)

        if figpath is not None:
            plt.savefig(figpath,bbox_inches='tight')

        return ax
