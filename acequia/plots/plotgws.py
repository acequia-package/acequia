#-------------------------------------------------------------------------------
# Purpose:     plot a single pandas time serie to file
# Author:      Thomas de Meij
# Created:     29-03-2013 updated 3-6-2014
# Licence:     Python 2.7 with pandas and matplotlib
#-------------------------------------------------------------------------------
from pandas import DataFrame, Series
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from math import ceil as ceil, floor as floor
import numpy as np
#import clsDINOGWS
from imp import reload
#reload(clsDINOGWS)
#from clsDINOGWS import dinogws
import os
import os.path
import datetime as dt
#inch = 25.4 mm
mm = 1/25.4


class PlotHeads:
    """Class for plotting customized graph of groundwater head series

    """

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
        }
    clr = clrs['rainbow']*10 # avoid out of bounds


    font1 = {
        'family' : 'serif',
        'color'  : 'darkred',
        'weight' : 'normal',
        'size'   : 8,
        }


    def __init__(self,ts=[],reference="datum",lbs=None,mps=None,
                 title=None,xlabel=None,ylabel=None,xlim=None,
                 ylim=None,plotargs=None):
        """ Plot list of groundwater head series in one graph

        Parameters
        ----------

        ts : list
            list of pd.Series with pd.DateTimeIndex

        reference : {'datum','surface','mp'}, default 'datum'
            reference level for groundwater heads

        lbs : list of strings, optional
            labels for heads series

        mps : pd.DataFrame
            

        title : string, optional
            title for graph

        xlabel : string, optional
            graph xaxis label

        ylabel :  string, optional
            graph yaxis label

        xlim : tuple or list, optional
            min and max of dates on xaxis

        ylim : tuple or list, optional
            min and max of heads on yaxis

        plotargs : list of dicts, optional
            dict of pyplot plotting parameters for each series
        
        Example
        -------
        gws  = aq.GwSeries.from_json(<json sourcefile>)
        sr   = gw.heads(ref='datum')
        plot = aq.PlotHeads(ts=[sr],ylim=[19.5,21.5])
            
             
        """

        self.ts = ts
        if not all(isinstance(sr, pd.Series) for sr in self.ts):
            msg = {f'Wrong input of timeseries. Expected a list of',
                   f'Pandas Series with DateTime indexes.'}
            raise TypeError(' '.join(msg))
        if not all(isinstance(sr.index, pd.DatetimeIndex) for sr in self.ts):
            msg = f'Index of series must be type DateTimeIndex'
            raise TypeError(msg)
        self._validate_series()


        self.reference = reference
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

        print(self.ylim)
        self._create_axes()
        print(self.ylim)
        self._plotlines()
        self._set_xaxlim()
        print(self.ylim)
        self._set_yaxlim()
        print(self.ylim)
        self._set_ticklabels()
        self._set_axlabels()
        self._set_legend()
        if self.mps is not None:
            self._reference_graph()
        self._plot_annotations()


    def __repr__(self):
        return "Plot multiple groundwater head time series"

    
    def fig(self):
        return self.fig

    def mindate(self):
        return np.array([(sr.index.date).min() for sr in self.ts]).min()


    def maxdate(self):
        return np.array([(sr.index.date).max() for sr in self.ts]).max()


    def nyears(self):
        return np.array([len(set(sr.index.year)) for sr in self.ts]).max()


    def _validate_series(self):
        for i,sr in enumerate(self.ts):
            if len(sr[sr.notnull()])==0:
                self.ts[i] = sr.fillna(0)
                # TODO: user warning

    def _create_axes(self):

        # create figure
        self.fig = plt.figure(facecolor='#eeefff')
        #self.fig = plt.figure(figsize=(9, 8), dpi= 80, facecolor='#eeefff', edgecolor='k')
        #plt.rcParams['figure.figsize'] = [10, 5]

        # Make all axes for figure
        if self.mps is None: ## and len(description)==0:
            # just groundwater level axes
            #self.axgws = self.fig.add_subplot(111)
            self._axgws = self.fig.add_axes([0.1,0.1,0.8,0.9])
            self.axeslist = {"axgws":self._axgws}
        else:
            # add graph wit reference and level height 
            #  [left, bottom, width, height] values in 0-1 relative figure coordinates:
            self._axmp  = self.fig.add_axes([0.1,0.77,0.8,0.15])
            self._axgws = self.fig.add_axes([0.1,0.1,0.8,0.65])
            self.axeslist = {"axmp":self._axmp,"axgws":self._axgws}



    def _plotlines(self):


        # plot all time series
        #ts.reverse()
        #lbs.reverse()
        plt.sca(self.axeslist['axgws'])

        if (self.mps is None) and (len(self.ts)==1):

            # plot only first roundwater series on bottom graph
            self.axeslist['axgws'] = self.ts[0].plot(color=self.clr[0],
                                     label=self.lbs[0])

        if (self.mps is None) and (len(self.ts)>1):
        ##    if (len(self.ts)!=0) and (self.lbs is not None):

            for i,sr in enumerate(self.ts):
                ##if len(self.plotargs)>=i+1:
                if not 'color' in self.plotargs[i].keys(): 
                    self.plotargs[i]['color']=self.clr[i]
                self._axgws = sr.plot(label=self.lbs[i], 
                                      **self.plotargs[i])
                ##else:
                ##    self._axgws = sr.plot(label=self.lbs[i],
                ##    color=self.colors[i])                            )


    def _set_yaxlim(self):
        """ Set yax limits for groundwater level """

        if self.ylim is None:
            #ymin,ymax = self.axeslist['axgws'].get_ylim()

            ymin = min([min(sr) for sr in self.ts])
            #ymin = (floor(ymin/10.))*10. # round to decimals
            
            ymax = max([max(sr) for sr in self.ts])
            #ymax = (ceil(ymax/10.))*10.  # round to decimals

            self.ylim = [ymin,ymax]

        self._axgws.set_ylim(self.ylim)

        if self.reference=="cmmv":
            self._axgws.set_ylim(self.ylim[::-1])
            ##plt.yticks(range(200,-50-10,10))


    def _set_xaxlim(self):
        """ Set xax limits for dates) """

        if self.xlim is None:
            self.xlim = [self.mindate(),self.maxdate()]
            self.xaxyears = self.nyears()
        else:
            if type(self.xlim[0])==str and type(self.xlim[1])==str:
                self.xlim[0] = dt.datetime.strptime(self.xlim[0],'%d-%m-%Y')
                self.xlim[1] = dt.datetime.strptime(self.xlim[1],'%d-%m-%Y')
            elif type(self.xlim[0])==int and type(self.xlim[1])==int:
                self.xlim[0] = dt.datetime(year=int(self.xlim[0]), 
                               month=1, day=1)
                self.xlim[1] = dt.datetime(year=int(self.xlim[1]), 
                               month=12, day=31)

            self.xaxyears = self.xlim[1].year-self.xlim[0].year+1


        # set xaxis date limits and locators
        for ax in self.axeslist:
            self.axeslist[ax].set_xlim(self.xlim)
            if self.xaxyears < 5:
                self.axeslist[ax].xaxis.set_major_locator(YearLocator(1, month=1,day=1))
                self.axeslist[ax].xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
                labels = ['apr','jul','okt']*5
                myfontdic = {'fontsize': 8}
                self.axeslist[ax].set_xticklabels(labels, fontdict=myfontdic, minor=True)

            elif self.xaxyears in range(5,10):
                self.axeslist[ax].xaxis.set_major_locator(YearLocator(1, month=1,day=1))
                
            elif self.xaxyears in range(10,25):
                self.axeslist[ax].xaxis.set_major_locator(YearLocator(5, month=1,day=1))
                self.axeslist[ax].xaxis.set_minor_locator(YearLocator(1, month=1,day=1))

            elif self.xaxyears in range(25,50):
                self.axeslist[ax].xaxis.set_major_locator(YearLocator(5, month=1,day=1))

            else:
                self.axeslist[ax].xaxis.set_major_locator(YearLocator(10, month=1,day=1))


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

        if len(self._lbs)!=0:
            plt.legend(shadow = False, loc = 4)
            #print(lbs)
            #plt.legend().get_frame().set_linewidth(0.0)
            self.axeslist['axgws'].legend(loc='lower left', 
                 ncol=4, bbox_to_anchor=(0., -0.20, 1., .15), 
                 mode="expand", borderaxespad=0.,frameon=False)
            #leg = plt.legend()

        # plot legend texts
        ltext = plt.gca().get_legend().get_texts()
        #print(ltext[0])
        for i in range(len(ltext)):
            plt.setp(ltext[i], fontsize = 9.0, color = 'k')


    def _reference_graph(self):

        # plot reference line on top graph
        self.mps["mpref"].plot(ax=self.axmp,color=colors[6],lw=2.)
        #mps["mvcmnap"].plot(ax=self.axmp,color=colors[1],lw=3.)
        
        # set x-axis equal to grondwwater series
        self.axmp.set_xlim(self.axgws.get_xlim())

        # set grid on
        self.axmp.grid(True,which="both",ls="-")
        
        # set y-ax limits on reference graph
        yrange = self.axmp.get_ylim()
        roundto = 10.
        min = (floor(yrange[0]/roundto))*roundto # round to decimals
        max = (ceil(yrange[1]/roundto))*roundto  # round to decimals
        self.axmp.set_ylim([min,max])

        # set yticks for reference graph
        self.axmp.yaxis.tick_right()            
        tks = self.axmp.get_yticks()
        tks = np.arange(tks.min(),tks.max()+1,(tks.max()-tks.min())/4.)
        self.axmp.set_yticks(tks)

        yticklabels = self.axmp.get_yticklabels()
        for i,label in enumerate(yticklabels):
            #label.set_color('k')
            #label.set_fontsize = 5.0
            if i in [0,2,4]: label.set_visible(True)
            else: label.set_visible(False)

        # Set x-ticklabels for mp graph invisible
        for label in self.axmp.get_xticklabels():
            label.set_visible(False)

        # set x-axis title for reference graph off
        self.axmp.set_xlabel('')


    def _plot_annotations(self):


        self._axgws.grid(True,which="major",ls="-")
        self._axgws.grid(True,which="minor",ls=":")

        if self.title and self.mps.empty:
            plt.text(0.0,1.02,title,transform=self.axgws.transAxes)
        elif self.title:
            plt.text(0.0,1.1,title,transform=self.axmp.transAxes)

        # plot datespan right of graph 90 degrees upward
        timespan = self.mindate().strftime("%d-%m-%Y")+" t/m " \
                   +self.maxdate().strftime("%d-%m-%Y")
        self.axeslist['axgws'].text(1.03, 0., timespan, 
             horizontalalignment='center',
             verticalalignment='bottom',rotation='vertical',
             transform=self.axeslist['axgws'].transAxes)


    def save(self,filename):
        # Save figure to file
        #fig = plt.figure(1)
        mydpi = 200.0 # default dpi is 100.0
        #mydpi = self.fig.dpi
        self.fig.set_dpi(mydpi)
        self.fig.set_size_inches(160*mm,80*mm)
        self.fig.savefig(filename,dpi=mydpi, facecolor='w', 
        edgecolor='w', bbox_inches="tight") #additional_artists=self.addart,
        #fig.close()
        #plt.clf() # open straks geen nieuwe plot (dat kost geheugen)
        # show plot
        #plt.show()
        #plt.close()




