
""" Class Headsdif has methods for calculating and plotting heads
differences between multiple groundwater series
"""

import warnings
import math

from pandas import Series, DataFrame
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import numpy as np

import acequia


def headsdif_from_gwseries(heads=None,locname=None,refcol=None):
    """Return HeadsDif object with data or None for invalid data

    Parameters
    ----------
    heads : list of GwSeries objects
        measured heads of multiple groundwater series
    locname : str
        location name for annotating graphs
    refcol : str, optional
        series name to use as reference

    Returns
    -------
    HeadsDif object or None

    Examples
    --------
    >>>hd = headsdif_from_gwseries(heads=<heads>,locname=<locname>,
            refcol=<refcol>)

    """


    if not isinstance(heads,list):
        msg = 'Parameter heads must be a list of GwSeries onjects'
        warnings.warn(msg)
        return None

    if not all([isinstance(x,acequia.gwseries.GwSeries) for x in heads]):
        msg = 'Parameter heads must be a list of GwSeries onjects'
        warnings.warn(msg)
        return None

    valid_heads = [x for x in heads if not x.heads().isnull().all()]
    if not len(valid_heads)==len(heads):
        removed = list(set(heads).difference(valid_heads))
        msg = f'Series {removed} with only NaNs removed from list'
        warnings.warn(msg)

    if len(valid_heads)<2:
        msg = 'Less than two heads series left after validation.'
        warnings.warn(msg)
        return None

    return HeadsDif(heads=valid_heads,locname=locname,refcol=refcol)


class HeadsDif:
    """Calculates head differences and descriptive statistics for 
    multiple groundwater head series

    Parameters
    ----------
    heads : list,pd.DataFrame
        measured heads of multiple groundwater series
    locname : str
        location name for annotating graphs
    refcol : str
        series name to use as reference

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

    _period_names = {'quarter','half-year'}


    def __repr__(self):
        nsr = len(self.table_headsdif().columns)
        return (f'{self.__class__.__name__}(n={nsr})')


    def __init__(self,heads=None,locname=None,refcol=None):

        if heads is None:
            msg = f'Parameter heads must be given'
            raise ValueError(msg)

        if isinstance(heads,list):

            if isinstance(heads[0],acequia.GwSeries):
                heads = [gw for gw in heads if not 
                         gw.heads().isnull().all()]

                tslist = [gw.heads(ref='datum',freq='D')
                          for gw in heads]

                if locname is None:
                    self.locname = heads[0].locname()

            if isinstance(heads[0],pd.Series):
                tslist = heads

            self._heads = pd.concat(tslist, axis=1)

        if isinstance(heads,pd.DataFrame):
            self._heads = heads

        if locname is None:
            self.locname = self._heads.columns[0].split('_')[0]
        self.locname = locname

        if refcol is None:
            refcol = list(self._heads)[0]
        self._refcol = refcol

        # create standard variables
        self._check_heads()
        self._headsdif = self.table_headsdif()
        self._headsref = self.table_headsref()


    def table_headsdif(self,ref=None):
        """Return table with head differences relative to series ref.
        If ref is not set, first series is taken as reference.

        Returns
        -------
        pd.DataFrame

        """

        if ref is None:
            ref = self._refcol

        if (ref not in self._heads.columns) and (ref is not None):
            msg = f'Reference column {ref} not in heads table.'
            warnings.warn(msg)

        heads = self._heads.copy()
        hdif = self._heads.copy()
        for i,col in enumerate(list(hdif)):
            hdif[col] = heads[col]-heads[ref]

        return hdif


    def table_headsref(self):
        """Return table with heads relative to mean of entire series"""
        heads = self._heads.copy()
        for i,col in enumerate(list(heads)):
            heads[col] = heads[col]-heads[col].mean()
        return heads


    def difsums(self,period='quarter'):
        """Return table with head differences by season

        Parameters
        ----------
        seasons : {'quarter','half-year'}
            aggregation level

        Returns
        -------
        pd.DataFrame

        """

        if period not in self._period_names:
            msg = ''.join(
                  f'{period} is not a valid period name. ',
                  f'Period must be in {self._period_names}.',)
            raise ValueError(msg)

        seasons = self.date_seasons(self._headsdif,period=period)
        difsns = (self._headsdif*100).groupby(seasons).mean().round(2).T
        difsns.columns.name = None
        difsns.index.name = 'series'
        return difsns


    def _check_heads(self):
        """Check heads measurement table for errors, repair and show
        warnings.""" 

        for col in self._heads.columns:
            allnull = self._heads[col].isnull().all()
            if allnull:
                self._heads = self._heads.drop(columns=[col])

        refcol_missing = self._refcol not in self._heads.columns
        ncols = len(self._heads.columns)
        if refcol_missing and ncols>1:
            old_refcol = self._refcol
            self._refcol = self._heads.columns[0]

            msg = f'Dropped reference column {old_refcol}, replaced with {self._refcol}'
            warnings.warn(msg)

        if ncols < 2:
            msg = f'Less than two columns with valid data in {self.locname}'
            raise ValueError(msg)


    def date_seasons(self,dtindex,period='quarter'):
        """Return list with seasons for each datetime in index

        Parameters
        ----------
        dtindex : pd.Datarame,pd.DateTimeIndex
            index with dates

        seasons : {'quarter','half-year'}
            aggregation level

        Returns
        -------
        list with season for each datetime

        """

        if isinstance(dtindex,pd.DataFrame):
            dtindex = dtindex.index

        if period=='quarter':
            seasons = ['1_Winter', '1_Winter', '2_Voorjaar', '2_Voorjaar', 
                       '2_Voorjaar', '3_Zomer', '3_Zomer', '3_Zomer', 
                       '4_Herfst', '4_Herfst', 
                       '4_Herfst', '1_Winter']
            month_to_season = dict(zip(range(1,13), seasons))
            seasons = dtindex.month.map(month_to_season).values

        if period=='half-year':
            seasons = ['Winter', 'Winter', 'Winter', 'Zomer', 'Zomer', 
                       'Zomer', 'Zomer', 'Zomer', 'Zomer', 'Winter', 
                       'Winter', 'Winter']
            month_to_season = dict(zip(range(1,13), seasons))
            seasons = dtindex.month.map(month_to_season).values

        return seasons


    def plot_time(self,figpath=None,figsize=None,colors=None):
        """Plot al heads in one graph and all head differences below that 
           in one figure """

        if figpath is None:
            msg = f'Parameter figpath must be given'
            raise ValueError(msg)

        if figsize is None:
            figsize = [12,18]

        if colors is None:
            colors = sns.color_palette('bright')

        nrows = len(list(self._heads))+1
        fig,axes = plt.subplots(nrows,1)
        plt.subplots_adjust(hspace=0.4)
        fig.set_figwidth(figsize[0])
        fig.set_figheight(figsize[1])

        for i,col in enumerate(list(self._heads)):

            title = f'{self.locname} (all series)'
            
            self._heads[col].dropna().plot(ax=axes[0],color=colors[i],
                                           title=title)
            #heads[col].plot(ax=axes[i+1])
            """
            if col==self._refcol:
                sr = self._headsref[col]*100
                title = f'{sr.name} (reference difference to mean)'
                sr.dropna().plot(ax=axes[i+1],color=colors[i],title=title)
                axes[i+1].yaxis.set_label_text('relatieve stijghoogte (cm)')
            else:
            """
            sr = self._headsdif[col]*100
            sr.dropna().plot(ax=axes[i+1],color=colors[i])

            axes[i+1].set_title(sr.name, fontsize='large')
            axes[i+1].yaxis.set_label_text('stijghoogteverschil (cm)')

            axes[i+1].axhline(y=0, color='darkgray',linestyle='--')

        for i in range(len(axes)):
                axes[i].set_xlabel(' ')
        #fig.suptitle(locname,fontsize=12)

        fig.savefig(figpath, dpi=300, facecolor='w', edgecolor='w')

        return fig,axes


    def plot_head(self,figpath=None,color='season'):
        """Plot head difference by reference head value """

        colnames = self._headsdif.columns

        if len(self._headsdif.columns) <= 2:
            ncols = 1
            nrows = 1
            figsize = (8.5,8.5)
        else:
            naxs = len(colnames)-1
            ncols = 2
            nrows = math.ceil(naxs/ncols)
            figsize = (8.5,4*nrows)

        fig, axs = plt.subplots(
                    nrows, ncols, squeeze=False, 
                    sharex=True, sharey=False,
                    figsize=figsize, dpi=100)

        axix = [(r,c) for r in range(nrows) for c in range(ncols)]

        if color=='half-year':
            seasons = self.date_seasons(self._headsdif,periods='half-year')
            coldict = {'Winter':'#0057e7','Zomer':'#ffa500'}
            colors = [coldict[x] for x in seasons]

        if color=='season':
            seasons = self.date_seasons(self._headsdif,period='quarter')
            coldict = {'1_Winter':'#0057e7', '2_Voorjaar':'#74d4f0',
                       '3_Zomer':'#ff0000','4_Herfst':'#ffa500'}
            colors = [coldict[x] for x in seasons]

        pal = sns.color_palette(colors)

        for i in range(len(colnames)-1):

            ax = axs[axix[i]]

            ax.axhline(y=0, color='darkgray',linestyle='--')
            ax.axvline(x=0, color='darkgray',linestyle='--')

            ax.axhline(y=5, color='slategray',linestyle='-.')
            ax.axhline(y=-5, color='slategray',linestyle='-.')

            data = self._headsdif
            data[self._refcol] = self._headsref[self._refcol]

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

            #plt.fill_between(
            #    ax.axhline(y=2.5, color='darkgray',linestyle='--'),
            #    ax.axhline(y=-2.5, color='darkgray',linestyle='--'),
            #    )

            #plt.fill_between([0.1,0.9],[0.1,0.9],
            #                 color='#ffff00', alpha=0.5)
            #ax.fill_between(x, y1, y2, where=y2 <= y1, facecolor='red', interpolate=True)
            #ax.plot(x, y1, x, y2, color='black')
            #        #facecolor='red', interpolate=True)

        fig.tight_layout()
        fig.savefig(figpath, dpi=300)

        return fig, axs


    def plot_freq(self):
        """Plot head differences as grid of frequency plots

        Returns
        -------
        fig,ax

        """

        loclist = list(self._headsdif.columns)
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

            tbl = self.table_headsdif(ref)
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

        return fig,axs

