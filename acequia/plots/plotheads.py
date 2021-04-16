#-------------------------------------------------------------------------------
# Purpose:     plot a single pandas time serie to file
# Author:      Thomas de Meij
# Created:     29-03-2013 updated 3-6-2014
# Licence:     Python 2.7 with pandas and matplotlib
#-------------------------------------------------------------------------------
import warnings
from math import ceil as ceil, floor as floor
import os
import os.path
import datetime as dt


from pandas import DataFrame, Series
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import matplotlib.dates as mdates

import numpy as np
#from imp import reload
import acequia as aq
#inch = 25.4 mm



class PlotHeads:
    """Class for plotting customized graph of groundwater head series

    """
    mm = 1/25.4

    # define line colors
    clrs = {
        'skytones': 
            ['#172458','#354898','#607cbd','#95b3d7','c','k','g'], # by rehenry
        'maximilian': 
            ['#d3d3d3','#e9e9e9','#a6bbca','#86a0b3','#65899d'], # by brynnreacjlocal
        'magazine2' : 
            ['#153f79','#79153f','#3f7915','#794f15','#1e1e1e'],
        'rainbow' : 
            ['#2347c5','#b41515','#1c9018','#ecee19','#ce11f2'],
        'easterpastel':
            ['#d666c6','#6e64db','#7ad89d','#67a3db','#dfe755'],
        'rainbow-adjusted':
            ['#2767fd','#d92950','#50d929','#ecee19','#ce11f2'],
        }



    font1 = {
        'family' : 'serif',
        'color'  : 'darkred',
        'weight' : 'normal',
        'size'   : 8,
        }


    def __init__(self,ts=[],ref="datum",lbs=None,mps=None,
                 title=None,xlabel=None,ylabel=None,xlim=None,
                 ylim=None,colors=None,plotargs=None,plot=True):
        """ Plot list of groundwater head series in one graph

        Parameters
        ----------

        ts : list
            list of pd.Series with pd.DateTimeIndex

        ref : {'datum','surface','mp'}, default 'datum'
            reference level for groundwater heads

        lbs : list of strings, optional
            labels for heads series

        mps : pd.Series
            Timeseries with change of measurement reference point level

        title : string, optional
            title for graph

        xlabel : string, optional
            graph xaxis label

        ylabel :  string, optional
            graph yaxis label

        xlim : tuple or list of TimeStamp,int or str, optional
            min and max of dates on xaxis

        ylim : tuple or list, optional
            min and max of heads on yaxis

        colors : list,optional
            valid pyplot colors for drawing lines

        plotargs : list of dicts, optional
            dict of pyplot plotting parameters for each series

        plot : boolean, default True
            plot heads immediately (if Flase, call PlotHeads.plotheads()

        Notes
        -----
        xlim can have several forms:
        [2009,2012] plots period 1-1-2009:31-12-2012
        alternative: ['01-01-2009','31-12-2012]
        alternative: [<pd.Timestamp>,<pd.Timestamp>]

        Examples
        --------
        gws  = aq.GwSeries.from_json(<json sourcefile>)
        sr   = gw.heads(ref='datum')
        plot = aq.PlotHeads(ts=[sr],ylim=[19.5,21.5])
        plot.save(<filename.jpg>,dpi=300.0)
             
        """

        self.reflist = ['datum','surface','mp']
        if ref not in self.reflist:
            msg = f'Reference level must be in {self.reflist} not {ref}'
            raise TypeError(msg)
        self.ref = ref

        self.ts = ts
        if all(isinstance(gw, aq.gwseries.GwSeries) for gw in ts):
            self.ts = [gw.heads(ref=self.ref) for gw in ts]
        if self.ref=='surface':
            self.ts = [ts*100 for ts in self.ts]

        if not all(isinstance(sr, pd.Series) for sr in self.ts):
            msg = {f'Wrong input of timeseries. Expected a list of',
                   f'Pandas Series with DateTime indexes.'}
            raise TypeError(' '.join(msg))

        if not all(isinstance(sr.index, pd.DatetimeIndex) for sr in self.ts):
            msg = f'Index of series must be type DateTimeIndex'
            raise TypeError(msg)

        if (not isinstance(mps, pd.Series)) and (mps is not None):
            msg = f'Time series {mps} with referennce changes must be pd.Series'
            raise TypeError(msg)

        if isinstance(colors,list):
            self.clr = colors*10
        else:
            self.clr = self.clrs['rainbow-adjusted']*10 # avoid out of bounds


        self._validate_series()

        self.xlim = xlim
        self.ylim = ylim
        self.mps = mps
        self.title = title
        self.ylabel = ylabel
        self.xlabel = xlabel

        if lbs is None:
            self.lbs = [sr.name for sr in self.ts]
        else:
            self.lbs = lbs

        if plotargs is None:
            self.plotargs = [{} for sr in self.ts]
        else:
            self.plotargs = plotargs

        if plot==True:
            self.plotheads()


    def __repr__(self):
        return "Plot multiple groundwater head time series"

    
    def fig(self):
        """Return figure """
        return self.fig

    def mindate(self):
        """Return very first date in list of heads series"""
        return np.array([(sr.index.date).min() for sr in self.ts]).min()


    def maxdate(self):
        """Return very last date in list of heads series"""
        return np.array([(sr.index.date).max() for sr in self.ts]).max()


    def nyears(self):
        """Return maximum number of years with measurements """
        return np.array([len(set(sr.index.year)) for sr in self.ts]).max()


    def _validate_series(self):
        """Replace all NaN values with zero"""
        for i,sr in enumerate(self.ts):
            if len(sr[sr.notnull()])==0:
                self.ts[i] = sr.fillna(0)
                # TODO: user warning


    def _create_axes(self):
        """Create figuer object with axes"""

        #self.fig = plt.figure(figsize=(9, 8), dpi= 80, facecolor='#eeefff', 
        #                        edgecolor='k')
        self.fig = plt.figure(figsize=(8, 5),facecolor='#eeefff')

        if self.mps is None: ## and len(description)==0:

            self._axmp = None
            self._axgws = self.fig.add_axes([0.1,0.1,0.8,0.9])
            self.axeslist = {"axgws":self._axgws}

        else:

            # add graph with reference and level height 
            #  [left, bottom, width, height] values in 0-1 relative figure coordinates:
            self._axmp  = self.fig.add_axes([0.1,0.77,0.8,0.15])
            self._axgws = self.fig.add_axes([0.1,0.1,0.8,0.65])

            self.axeslist = {"axmp":self._axmp,"axgws":self._axgws}


    def plotheads(self,title=None,xlabel=None,ylabel=None,xlim=None,
        ylim=None,colors=None):
        """Plot groundwater heads and reference graph"""

        if title is not None:
            self.title = title

        if xlabel is not None:
            self.xlabel = xlabel

        if ylabel is not None:
            self.ylabel = ylabel

        if xlim is not None:
            self.xlim = xlim
            ##self._set_xaxlimits(xlim)
            self._set_xlim(xlim)

        if ylim is not None:
            self.ylim = ylim
            #self._set_yax_limits()

        if colors is not None:
            self.colors = colors

        self._create_axes()
        #ts.reverse()
        #lbs.reverse()

        # plot groundwater heads in lower plot
        for i,sr in enumerate(self.ts):

            if not 'color' in self.plotargs[i].keys(): 
                self.plotargs[i]['color']=self.clr[i]
            self.plotargs[i]['lw']=0.9


            self._axgws = sr.dropna().plot(label=self.lbs[i], 
                                  **self.plotargs[i])

        # adjust plot appearance
        self._set_xax_limits(xlim=self.xlim)
        self._set_xax_locators()
        self._set_yax_limits()
        self._set_ticklabels()
        self._set_axlabels()
        self._set_legend()
        self._plot_annotations()

        # plot reference change in upper plot
        if self.mps is not None:
            self._reference_graph()


    def _set_yax_limits(self):
        """ Set yax limits for groundwater level """

        if self.ylim is None:

            ymin = min([min(sr.dropna()) for sr in self.ts])
            ymax = max([max(sr.dropna()) for sr in self.ts])

            if ymin==0 and ymax==0: #all series are empty
                ymin = -1.0
                ymax = 1.0

            #ymin = (floor(ymin/10.))*10. # round to decimals
            #ymax = (ceil(ymax/10.))*10.  # round to decimals

            self.ylim = [ymin,ymax]

        self._axgws.set_ylim(self.ylim)

        if self.ref=="surface":
            self._axgws.set_ylim(self.ylim[::-1])


    def _set_xlim(self,xlim=None):
        """Set xlim (mindate,maxdate)"""

        if xlim is None:
            xlim = [self.mindate(),self.maxdate()]

        if not isinstance(xlim,list):
            warnings.warn(f'xlim must be list [mindate,maxdate] '
                f'not {type(xlim)} ')
            xlim = [self.mindate(),self.maxdate()]

        if xlim[0] is None:
            xlim[0] = self.mindate()

        if xlim[1] is None:
            xlim[1] = self.maxdate()

        if isinstance(xlim[0],str):
            xlim[0] = dt.datetime.strptime(xlim[0],'%d-%m-%Y')

        if isinstance(xlim[1],str):
            xlim[1] = dt.datetime.strptime(xlim[0],'%d-%m-%Y')

        if isinstance(xlim[0],int):
            xlim[0] = dt.datetime(year=int(xlim[0]), month=1, day=1)

        if isinstance(xlim[1],int):
            xlim[1] = dt.datetime(year=int(xlim[1]), month=1, day=1)

        """
        if type(self.xlim[0])==str and type(self.xlim[1])==str:
            self.xlim[0] = dt.datetime.strptime(self.xlim[0],'%d-%m-%Y')
            self.xlim[1] = dt.datetime.strptime(self.xlim[1],'%d-%m-%Y')

        if type(self.xlim[0])==int and type(self.xlim[1])==int:
            self.xlim[0] = dt.datetime(year=int(self.xlim[0]), 
                           month=1, day=1)
            self.xlim[1] = dt.datetime(year=int(self.xlim[1]), 
                           month=12, day=31)
        """
        self.xlim = xlim

    def _set_xax_limits(self,xlim=None):
        """ Set xax limits for dates) """

        self._set_xlim(xlim)

        for ax in self.axeslist:
            self.axeslist[ax].set_xlim(self.xlim)


    def _set_xax_locators(self):

        # set xaxis date locators
        self.xaxyears = self.xlim[1].year-self.xlim[0].year+1
        for ax in self.axeslist:
            self.axeslist[ax].set_xlim(self.xlim)

            years = mdates.YearLocator()   # every year
            months = mdates.MonthLocator()  # every month
            years_fmt = mdates.DateFormatter('%Y')

            self.axeslist[ax].xaxis.set_major_formatter(years_fmt)

            ##print(f'self.xaxyears is {self.xaxyears}')

            ##plt.rcParams['dates.epoch'] = '0000-12-31'
            ##dt.set_epoch = '0000-12-31'

            if self.xaxyears in range(0,3):
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(1, month=1,day=1))
                self.axeslist[ax].xaxis.set_major_formatter(years_fmt)
                     #YearLocator(1, month=1,day=1))
                     #YearLocator(byyear=1))
                self.axeslist[ax].xaxis.set_minor_locator(
                     MonthLocator(bymonth=[1,4,7,10]))
                labels = ['jan','apr','jul','okt']*3
                myfontdic = {'fontsize': 4}
                self.axeslist[ax].set_xticklabels(labels, 
                     fontdict=myfontdic, minor=True)

            
            if self.xaxyears in range(3,5):

                #pass
                #"""
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(1, month=1,day=1))
                self.axeslist[ax].xaxis.set_major_formatter(years_fmt)

                
                self.axeslist[ax].xaxis.set_minor_locator(
                     MonthLocator(bymonth=[4,7,10]))
                labels = ['apr','jul','okt']*5
                myfontdic = {'fontsize': 8}
                self.axeslist[ax].set_xticklabels(labels, 
                     fontdict=myfontdic, minor=True)
                #"""

                #self.axeslist[ax].xaxis.set_major_formatter(
                #    DateFormatter('%y')) #%m-%d'))


            if self.xaxyears in range(5,11):
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(1, month=1,day=1))
                self.axeslist[ax].xaxis.set_major_formatter(years_fmt)
                self.axeslist[ax].xaxis.set_minor_locator(
                     YearLocator(1, month=1,day=1))


            if self.xaxyears in range(11,25):
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(5, month=1,day=1))
                self.axeslist[ax].xaxis.set_minor_locator(
                     YearLocator(1, month=1,day=1))

            if self.xaxyears in range(25,50):
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(5, month=1,day=1))

            if self.xaxyears in range(50,1000):
                self.axeslist[ax].xaxis.set_major_locator(
                     YearLocator(10, month=1,day=1))


    def _set_ticklabels(self):
    
        for label in self._axgws.get_xticklabels():
            label.set_color('k')
            label.set_fontsize = 5.0
            label.set_visible(True)
            label.set_rotation(0)
            label.set_horizontalalignment('center')

        for label in self._axgws.get_yticklabels():
            label.set_color('k')
            label.set_fontsize = 5.0
            label.set_visible(True)


    def _set_axlabels(self):

        if self.ylabel:
            plt.ylabel(self.ylabel, size = 11.0)
        else:
            plt.ylabel('grondwaterstand',size = 11.0)

        self.axeslist['axgws'].set_xlabel('')


    def _set_legend(self):

        # define legend labels
        self._lbs = [series.name for series in self.ts]
        if len(self._lbs)==0:
            return None

        ##plt.legend(shadow = False, loc = 4)

        # calculate position of legend
        if len(self._lbs)<=4:
            ncol=4
            bbox = [0., -0.20, 1., .15]
        elif len(self._lbs)<=8:
            ncol=4
            bbox = [0., -0.25, 1., .15]

        # explanation bbox:
        # plt.legend(bbox_to_anchor=(x0, y0, width, height), loc=4
        # width and height are the width and the height of the 
        # legend box, and (x0, y0) is the coordinate of the loc of 
        # the bounding box. loc=4 is lower right

        self.axeslist['axgws'].legend(loc='lower center', 
             ncol=ncol, bbox_to_anchor=(bbox), 
             mode="expand", borderaxespad=0.,frameon=False)

        # plot legend texts
        ##ltext = plt.gca().get_legend().get_texts()
        ltext = self.axeslist['axgws'].get_legend().get_texts()
        for i in range(len(ltext)):
            plt.setp(ltext[i], fontsize = 8.0, color = 'k')

        # set the linewidth of each legend object
        """
        leg = self.axeslist['axgws'].get_legend()
        for legobj in leg.legendHandles:
            legobj.set_linewidth(2.0)
        """

        leg = self.axeslist['axgws'].get_legend()
        for line in leg.get_lines():
            line.set_linewidth(2.5)


    def _reference_graph(self):
        """ Plot timeseries with relative changes """

        # plot reference line on top graph
        self.mps.plot(ax=self._axmp, color=self.clr[1],
                      lw=1.5)

        # set x-axis equal to grondwwater series
        self._axmp.set_xlim(self.xlim)

        # set grid on
        self._axmp.grid(True,which="both",ls="-")

        # x-ticklabels for mp graph invisible
        for label in self._axmp.get_xticklabels():
            label.set_visible(False)

        # x-axis title for reference graph invisible
        self._axmp.set_xlabel('')


    def _plot_annotations(self):
        """ Plot figure title and measurment periode """

        self._axgws.grid(True,which="major",ls="-")
        self._axgws.grid(True,which="minor",ls=":")

        if self.title and (self.mps is None):
            plt.text(0.0,1.02,self.title,transform=self._axgws.transAxes)
        elif self.title:
            plt.text(0.0,1.1,self.title,transform=self._axmp.transAxes)

        # plot datespan right of graph 90 degrees upward
        #timespan = self.mindate().strftime("%d-%m-%Y")+" t/m " \
        #           +self.maxdate().strftime("%d-%m-%Y")
        timespan = self.xlim[0].strftime("%d-%m-%Y")+" t/m " \
                   +self.xlim[1].strftime("%d-%m-%Y")

        self.axeslist['axgws'].text(1.03, 0., timespan, 
             horizontalalignment='center',
             verticalalignment='bottom',rotation='vertical',
             transform=self.axeslist['axgws'].transAxes)


    def save(self,filename,dpi=None):
        """Save figure to file

        Parameters
        ----------
        filename : str
            filename for saving figure (including extension)

        dpi : number, default 200.0
            dpi for output figure

        """

        if dpi is None:
            dpi = 200.0 # default dpi is 100.0
        self.fig.set_dpi(dpi)
        self.fig.set_size_inches(160*self.mm,80*self.mm)
        self.fig.savefig(
                filename,dpi=dpi, 
                facecolor='w', 
                edgecolor='w', 
                bbox_inches="tight") #additional_artists=self.addart,

