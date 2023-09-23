""" 
This module contains the class HeadsDiff for calculating and plotting 
differences between multiple groundwater head series.
"""

import warnings
import math
import numpy as np
from pandas import Series, DataFrame
from pandas import DatetimeIndex
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib as mpl
import seaborn as sns; sns.set()

from .gwseries import GwSeries



class HeadsDif:
    """Calculate head differences and descriptive statistics for 
    multiple groundwater head series

    Methods
    -------
    table_headsdif
        Return table with head differences relative to series ref.
    table_headsref
        Return table with heads relative to mean of entire series.
    difsums
        Return table with head differences by season.
    date_seasons
        Return list with seasons for each datetime in index.
    plot_time
        Plot al heads in one graph and all head differences below that 
        in one figure.
    plot_head
        Plot head difference by reference head value.
    plot_freq
        Plot head differences as grid of frequency plots.

    Notes
    -----
    Class HeadsDif requires input of a list of multiple GwSeries objects
    or pd.Series objects with valid head data. No checking is performed.

    To check input data before creating a HeadsDif object, us the custom
    function headsdif_from_gwseries(). This function returns None when 
    no valid heads could be calculated. 

    Examples
    --------
    Create headdiff object without checking input:
    >>>hd = acequia.headsdif(heads=<list>,locname=<str>, refcol=<str>)

    Call function headsdif_from_gwseires() and clean up data before
    creating a headsdiff object:
    >>>hd = headsdif_from_gwseries(heads=<heads>,locname=<locname>,
            refcol=<refcol>)
    >>>if hd is None:
    >>>     continue
    """


    FOURSEASONSKEY = 'seasons'
    FOURSEASONS = ['Winter','Winter','Spring','Spring',
        'Summer','Summer','Summer','Summer','Autumn', 
        'Autumn','Autumn', 'Winter',]
    FOURSEASONS_COLORS =  {'Winter':'#0057e7', 'Spring':'#74d4f0',
        'Summer':'#ff0000','Autumn':'#ffa500'}
    FOURSEASONS_COLNAMES = ['Spring','Summer','Autumn','Winter']
    TWOSEASONSKEY = 'biannual'
    TWOSEASONS = ['Winter', 'Winter', 'Winter', 'Summer', 'Summer', 
        'Summer', 'Summer', 'Summer', 'Summer', 'Winter', 'Winter', 
        'Winter']
    TWOSEASONS_COLORS = {'Winter':'#2196f3','Summer':'#ffb74d'}
    PERIOD_DEFAULT = FOURSEASONSKEY
    PERIOD_NAMES = {FOURSEASONSKEY,TWOSEASONSKEY}

    MPL_STYLE_DEFAULT = 'seaborn-v0_8-darkgrid'


    def __init__(self,heads=None,locname=None,refcol=None):
        """
        Parameters
        ----------
        heads : pd.DataFrame
            Measured heads of multiple groundwater series.
        locname : str, optional
            Location name for annotating graphs.
        refcol : str, optional
            Series name to use as reference.

        Notes
        -----
        If no values are given for parameters locname and refcol, 
        values will be derived from the first column in heads.
        """

        # validate heads
        if not isinstance(heads,DataFrame):
            raise ValueError((f'Init {self.__class__.__name__}: '
                f'Parameter heads must be a Pandas DataFrame, not '
                f'a {heads.__class__.__name__}.'))
        self.heads = heads

        # validate locname
        if locname is None:
            locname = list(self.heads)[0]
        if '_' in locname:
            locname = locname.split('_')[0]
        self.locname = locname

        # drop empty columns
        for col in self.heads.columns:
            if self.heads[col].isnull().all():
                self.heads = self.heads.drop(columns=[col])

        if len(list(self.heads)) < 2:
            msg = f'Less than two columns with valid data in {self.locname}'
            raise ValueError(msg)

        # validate refcol
        if refcol is None:
            refcol = list(self.heads)[0]
        self.refcol = refcol

        if self.refcol not in list(self.heads):
            old_refcol = self.refcol
            self.refcol = list(self.heads)[0]
            warnings.warn((f'Dropped reference column {old_refcol}, '
                f'replaced with {self.refcol}'))


    def __repr__(self):
        nsr = len(self.heads.columns)
        return (f'{self.__class__.__name__}({nsr} series)')


    @classmethod
    def from_series(cls,heads=None,locname=None,refcol=None):
        """Create HeadsDif object from list of GwSeries objects.

        Parameters
        ----------
        heads : list of GwSeries objects
            Measured heads of multiple groundwater series.
        locname : str, optional
            Location name for annotating graphs, optional.
        refcol : str, optional
            Series name to use as reference.

        Returns
        -------
        HeadsDiff
            HeadsDif object

        Examples
        --------
        >>>hd = HeadsDif.from_gwseries(heads=<heads>,locname=<locname>,
                refcol=<refcol>)

        Notes
        -----
        If no values are given for paramaters locname and refcol, 
        values will be used from the first GwSeries or Series in heads.
        """

        is_no_list_warning = ((f'Parameter heads must be a list of '
            f'GwSeries or Pandas Series objects'))

        if not isinstance(heads,list):
            raise ValueError(is_no_list_warning)

        if isinstance(heads[0],GwSeries):

            if not all([isinstance(x,GwSeries) for x in heads]):
                raise ValueError(is_no_list_warning)

            ##tslist = [gw.heads(ref='datum',freq='D') for gw in heads]
            if locname is None:
                locname = heads[0].locname()
            if refcol is None:
                refcol = heads[0].name()
            heads = [gw.heads() for gw in heads]
            """
            valid_heads = [x for x in heads if not x.heads().isnull().all()]
            if not len(valid_heads)==len(heads):
                removed = list(set(heads).difference(valid_heads))
                warnings.warn((f'Removed following heads series with only '
                    f'NaN valuess: {removed}.'))

            if len(valid_heads)<2:
                msg = 'Less than two heads series left after validation.'
                warnings.warn(msg)
                return None
            """

        if not all([isinstance(x,Series) for x in heads]):
            warnings.warn(is_no_list_warning)
            return None

        headstable = pd.concat(heads, axis=1)
        return HeadsDif(heads=headstable,locname=locname,refcol=refcol)


    def get_relative_heads(self):
        """Return table with heads relative to mean of entire series."""
        relheads = self.heads.copy()
        for i,col in enumerate(list(self.heads)):
            relheads[col] = self.heads[col]-self.heads[col].mean()
        return relheads


    def get_difference(self,refcol=None):
        """Return table with head differences.

        Parameters
        ----------
        refcol : str, optional
            Head differences will be calculated relative to this column.

        Returns
        -------
        pd.DataFrame
        """
        if refcol is None:
            refcol = self.refcol

        if (refcol not in self.heads.columns):
            firstcol = list(self.heads)[0]
            warnings.warn((f'Reference column {refcol} not in heads '
                f'table. First column "{firstcol}" will be used.'))
            refcol = firstcol

        hdif = self.heads.copy()
        for i,col in enumerate(list(hdif)):
            hdif[col] = self.heads[col]-self.heads[refcol]
        return hdif


    def get_seasons(self,dates=None,period=PERIOD_DEFAULT):
        """
        Return list with seasons for each datetime in index.

        Parameters
        ----------
        dates : pd.DataFrame, pd.DateTimeIndex, optional
            Index with dates.

        period : {'seasons','biannual'}, default 'seasons'
            Aggregate by seasons or by half-year.

        Returns
        -------
        numpy array
            Season for each datetime in dates
        """
        if dates is None:
            dates = self.heads

        if isinstance(dates,pd.DataFrame):
            dtindex = dates.index

        if isinstance(dates,pd.Series):
            dtindex = dates.index

        if isinstance(dates,DatetimeIndex):
            dtindex = dates

        if period not in self.PERIOD_NAMES:
            warnings.warn((f"Period '{period}' not in {self.PERIOD_NAMES},"
                "Default {self.PERIOD_DEFAULT} will be used."))
            period = self.PERIOD_DEFAULT

        if period==self.FOURSEASONSKEY:
            month_to_season = dict(zip(range(1,13), self.FOURSEASONS))
            seasons = dtindex.month.map(month_to_season).values

        if period==self.TWOSEASONSKEY:

            month_to_season = dict(zip(range(1,13), self.TWOSEASONS))
            seasons = dtindex.month.map(month_to_season).values

        return seasons


    def get_difference_by_season(self,period=PERIOD_DEFAULT):
        """Return table with head differences grouped by season.

        Parameters
        ----------
        seasons : {'seasons','biannual'}, default 'seasons'
            Aggregate by season or by half-year.

        Returns
        -------
        pd.DataFrame
        """
        headsdif = self.get_difference()
        seasons = self.get_seasons(headsdif,period=period)
        difsns = (headsdif*100).groupby(seasons).mean().round(2).T
        difsns.columns.name = None
        difsns.index.name = 'series'
        if period==self.FOURSEASONSKEY:
            difsns = difsns[self.FOURSEASONS_COLNAMES]
        return difsns

    @mpl.rc_context(plt.style.use(MPL_STYLE_DEFAULT))
    def plot_time(self,figpath=None,figsize=None,colors=None):
        """Plot al heads in one graph and all head differences below that 
           in one figure 
           
        Parameters
        ----------
        figpath : str
            Valid filepath for output figure.
        figsize : [width,height]
            Figure size in inches.
        colors : list of tuples or strings
            Colors for head lines (RGB tuples or Hexcodes).

        Returns
        -------
        axes
        """

        headsdif = self.get_difference()
        seasons = self.get_seasons(dates=headsdif,period='biannual')

        # colors for heads lines
        if colors is None:
            cm = mpl.colormaps['tab10_r'].reversed() #mpl colormap
            colorlist = cm.colors #list of RGB-tuples
            
            colors = {}
            for i,col in enumerate(list(headsdif)):
                colors[col] = colorlist[i]

        # colors for seasonal colored differences
        """
        cm2 = mpl.colormaps['tab10_r']
        season_colors ={
            'Winter':cm2.colors[0],
            'Summer':cm2.colors[2],
            }
        """
        season_colors = self.TWOSEASONS_COLORS

        # figure settings
        nrows = len(list(self.heads))
        fig,axs = plt.subplots(nrows=nrows,ncols=1,sharex=True,constrained_layout=True)
        if figsize is None:
            figsize = [7,5]
        fig.set_figwidth(figsize[0])
        fig.set_figheight(figsize[1])
        ##plt.subplots_adjust(hspace=0.4)

        # plot heads on first ax
        for col in list(self.heads):
            heads = self.heads[col].dropna().squeeze()
            #heads.plot(ax=axs[0],color=colors[col])
            axs[0].plot(heads.index,heads,label=col,color=colors[col])
        axs[0].set_title(label=f'Location {self.locname}',fontsize=10.)
        axs[0].yaxis.set_label_text('stijghoogte', fontsize=7.)
        ncols = min(len(list(self.heads)),4)
        legend = axs[0].legend(loc='upper left', bbox_to_anchor=(0.0, 0.0),
            fancybox=False, shadow=False, edgecolor="white",
            ncols=ncols,fontsize=7.)
        legend.get_frame().set_alpha(None)
        legend.get_frame().set_facecolor((0, 0, 0, 0.0))

        # plot head differences on next axes
        colnames = [x for x in list(self.heads) if x!=self.refcol]
        for i,col in enumerate(colnames):

            sr = headsdif[col].dropna()*100
            periods = self.get_seasons(dates=sr,period='biannual')
            srw = sr[periods=='Winter']
            srs = sr[periods=='Summer']

            srw.plot(ax=axs[i+1],color=season_colors['Winter'],style='.',ms=2,label='winter')
            srs.plot(ax=axs[i+1],color=season_colors['Summer'],style='.',ms=2,label='zomer')

            axs[i+1].axhline(y=0, color='darkgray',linestyle='--')
            titletext = f'stijghoogteverschil {sr.name} met {self.refcol}'
            axs[i+1].set_title(titletext, fontsize=10.)
            axs[i+1].yaxis.set_label_text('stijghoogteverschil (cm)', fontsize=7.)

            axs[i+1].legend(['winter', 'zomer',], loc='lower left',ncols=2,edgecolor=None)

        # xax formatter
        half_year_locator = mdates.MonthLocator(bymonth=(4, 10))
        year_month_formatter = mdates.DateFormatter("%m\n%Y")
        for i in range(len(axs)):

            axs[i].set_xlabel(' ')
            axs[i].tick_params(axis='y', labelsize=7.)
            axs[i].tick_params(axis='x', which='both', bottom=False, labelsize=9.)

            if i==len(axs)-1: #last axis only
                axs[i].xaxis.set_major_locator(half_year_locator) # Locator for major axis only.
                axs[i].xaxis.set_major_formatter(year_month_formatter) # formatter for major axis only
                axs[i].xaxis.set_minor_locator(mdates.MonthLocator())
        
        for i in range(len(axs)):

                for label in axs[i].get_xticklabels(which='major'):
                    label.set(rotation=0, horizontalalignment='center')

        if figpath is not None:
            fig.savefig(figpath, dpi=300, facecolor='w', edgecolor='w')

        return axs

    @mpl.rc_context(plt.style.use(MPL_STYLE_DEFAULT))
    def plot_head(self,figsize=None,figpath=None,period='biannual'):
        """Plot head difference by reference head value.

        Parameters
        ----------
        figpath : str, optional

        period : {'seasonal,'biannual'}, default 'season'

        """
        headsdif = self.get_difference()
        relheads = self.get_relative_heads()
        colnames = headsdif.columns

        # create fig, ax
        if figsize is None:
            figsize=(8.5,8.5)

        if len(headsdif.columns) <= 2:
            ncols = 1
            nrows = 1
            figsize = figsize
        else:
            naxs = len(colnames)-1
            ncols = 2
            nrows = math.ceil(naxs/ncols)
            figsize = (figsize[0],figsize[1]/2*nrows)

        fig, axs = plt.subplots(
                    nrows, ncols, squeeze=False, 
                    sharex=True, sharey=False,
                    figsize=figsize, dpi=100)

        ax_idx = [(r,c) for r in range(nrows) for c in range(ncols)]

        if period=='biannual':
            #seasons = self.date_seasons(self._headsdif,periods='half-year')
            seasons = self.get_seasons(dates=headsdif,period='biannual')
            coldict = self.TWOSEASONS_COLORS
            colors = [coldict[x] for x in seasons]

        if period=='season':
            #seasons = self.date_seasons(self._headsdif,period='quarter')
            seasons = self.get_seasons(dates=headsdif,period='biannual')
            coldict = self.FOURSEASONS_COLORS
            colors = [coldict[x] for x in seasons]

        pal = sns.color_palette(colors)

        for i in range(len(colnames)-1):

            ax = axs[ax_idx[i]]

            ax.axhline(y=0, color='darkgray',linestyle='--')
            ax.axvline(x=0, color='darkgray',linestyle='--')

            ax.axhline(y=5, color='slategray',linestyle='-.')
            ax.axhline(y=-5, color='slategray',linestyle='-.')

            data = headsdif
            data[self.refcol] = relheads[self.refcol]

            ax = sns.scatterplot(
                    x = colnames[0], 
                    y = colnames[i+1], 
                    data=data*100, 
                    ax=ax,
                    #color=colors[i+1])
                    palette=coldict,
                    hue = seasons)

            handles, labels = ax.get_legend_handles_labels()
            # sort both labels and handles by labels
            labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
            ax.legend(handles, labels)

            ax.set_title(colnames[i+1])
            xlab = f'relatieve stijghoogte {colnames[0]} (cm)'
            ax.xaxis.set_label_text(xlab)
            ylab = 'stijghoogteverschil (cm)'
            ax.yaxis.set_label_text(ylab)

        fig.tight_layout()
        if figpath:
            fig.savefig(figpath, dpi=300)

        return axs

    @mpl.rc_context(plt.style.use(MPL_STYLE_DEFAULT))
    def plot_freq(self):
        """
        Plot head differences as grid of frequency plots.

        Returns
        -------
        fig,ax
        """
        headsdif = self.get_difference()
        ##ref = self.ref

        loclist = list(headsdif.columns)
        nrows = len(loclist)
        ncols = len(loclist)
        fig, axs = plt.subplots(nrows=nrows,ncols=ncols,sharex=True)

        # space between subplots
        plt.tight_layout()
        bbox = axs[0,0].get_position()
        hpad = bbox.width/100.*10.
        vpad = bbox.height/100.*10.
        plt.subplots_adjust(bottom=0.1,top=0.9,left=0.1,wspace=vpad, 
                            hspace=hpad)

        for i,ref in enumerate(loclist):

            tbl = headsdif  #(ref)
            for j,col in enumerate(loclist):
                x = (tbl[col]-tbl[col].mean()).values*100
                
                xmax=22.5
                dx = 5.

                nbars = math.ceil((xmax-dx/2)/dx)
                xup = nbars*dx+dx/2
                xlow = -xmax
                
                bin_list = np.arange(xlow,xup+1,dx)
                n, bins, patches = axs[i,j].hist(x, bin_list, density=1,)

                # color of rectangles (this is a slow solution)
                for k,pt in enumerate(patches):
                    if k < len(bin_list)/2-1:
                        pt.set_facecolor('#4ca3dd')
                    elif k == len(bin_list)/2-1:
                        pt.set_facecolor('#ccdee9') # #c0d6e4
                    else:
                        pt.set_facecolor('#ff7f50')

                axs[i,j].set_yticks([])
                axs[i,j].set_xticks([])

                if i==0:
                    axs[i,j].set_title(f'{col}',fontsize=18)
                if j==0:
                    axs[i,j].set_ylabel(f'{ref}',fontsize=18)

                # title below graphs
                if i ==nrows-1:
                    bbox = axs[i,j].get_position()
                    vpad = bbox.height/10.
                    mid = bbox.xmin+bbox.width/2.
                    plt.figtext(mid,bbox.ymin-vpad,f'{dx} cm',
                                fontsize='large',
                                horizontalalignment='center')

        return axs
