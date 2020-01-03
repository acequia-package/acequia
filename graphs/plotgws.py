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



class PlotGws:

    def __init__(self):
        
        self.font1 = {'family' : 'serif',
        'color'  : 'darkred',
        'weight' : 'normal',
        'size'   : 8,
        }

    def __repr__(self):
        return "Grafieken van grondwaterstandsreeksen"
        
        
    def plotseries(self,ts=[],reference="cmnap",mps=DataFrame(),
                   description=[],title=None,xlabel=None,
                   ylabel=None,xlim=[],ylim=[],plotargs=[]):
        """ Tijdstijghoogtelijn op basis van lijst met series (datum,gws) 
            variable reference can be: "cmnap", "cmmv" or "cmmp"
        """

        def create_axes(mps):

            # Make all axes for figure
            if mps.empty: ## and len(description)==0:
                # just groundwater level axes
                #self.axgws = self.fig.add_subplot(111)
                self.axgws = self.fig.add_axes([0.1,0.1,0.8,0.9])
                self.axelist = {"axgws":self.axgws}
            else:
                # add graph wit reference and level height 
                #  [left, bottom, width, height] values in 0-1 relative figure coordinates:
                self.axmp  = self.fig.add_axes([0.1,0.77,0.8,0.15])
                self.axgws = self.fig.add_axes([0.1,0.1,0.8,0.65])
                self.axelist = {"axmp":self.axmp,"axgws":self.axgws}

        def set_axlim():
            """ Set ax limits for xax (dates) and yax (groundwater level) """

            # calculate y-axis limits
            if len(self.ylim)==0:
                ymin,ymax = self.axgws.get_ylim()
                ymin = (floor(ymin/10.))*10. # round to decimals
                ymax = (ceil(ymax/10.))*10.  # round to decimals
                self.ylim = [ymin,ymax]

            # set yaxis limits
            if self.reference=="cmnap": 
                self.axgws.set_ylim(self.ylim)
            elif self.reference=="cmmv":
                self.axgws.set_ylim(self.ylim[::-1])
                ##plt.yticks(range(200,-50-10,10))

            # calculate xaxis date limits
            if len(self.xlim)==0:
                self.xlim = [self.mindate,self.maxdate]
                self.xaxyears = self.nyears
            else:
                if type(self.xlim[0])==str and type(self.xlim[1])==str:
                    self.xlim[0] = dt.datetime.strptime(self.xlim[0],'%d-%m-%Y')
                    self.xlim[1] = dt.datetime.strptime(self.xlim[1],'%d-%m-%Y')
                elif type(self.xlim[0])==int and type(self.xlim[1])==int:
                    self.xlim[0] = dt.datetime(year=int(self.xlim[0]), month=1, day=1)
                    self.xlim[1] = dt.datetime(year=int(self.xlim[1]), month=12, day=31)
                self.xaxyears = self.xlim[1].year-self.xlim[0].year+1

            # set xaxis date limits and locators
            for ax in self.axelist:
                self.axelist[ax].set_xlim(self.xlim)
                if self.xaxyears < 5:
                    self.axelist[ax].xaxis.set_major_locator(YearLocator(1, month=1,day=1))
                    self.axelist[ax].xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
                    labels = ['apr','jul','okt']*5
                    myfontdic = {'fontsize': 8}
                    self.axelist[ax].set_xticklabels(labels, fontdict=myfontdic, minor=True)
                elif self.xaxyears in range(5,10):
                    self.axelist[ax].xaxis.set_major_locator(YearLocator(1, month=1,day=1))
                    
                elif self.xaxyears in range(10,25):
                    self.axelist[ax].xaxis.set_major_locator(YearLocator(5, month=1,day=1))
                    self.axelist[ax].xaxis.set_minor_locator(YearLocator(1, month=1,day=1))
                elif self.xaxyears in range(25,50):
                    self.axelist[ax].xaxis.set_major_locator(YearLocator(5, month=1,day=1))
                else:
                    self.axelist[ax].xaxis.set_major_locator(YearLocator(10, month=1,day=1))

            # grid for groundwater water level graph
            self.axgws.grid(True,which="major",ls="-")
            self.axgws.grid(True,which="minor",ls=":")


        def reference_graph():

            # plot reference line on top graph
            mps["mpref"].plot(ax=self.axmp,color=colors[6],lw=2.)
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

        # set variables to self
        self.ts = ts
        self.reference = reference
        self.xlim = xlim
        self.ylim = ylim

        # determine maximum and minimum date for xaxis
        if all(isinstance(sr.index, pd.DatetimeIndex) for sr in self.ts):
            self.mindate = np.array([(sr.index.date).min() for sr in self.ts]).min()
            self.maxdate = np.array([(sr.index.date).max() for sr in self.ts]).max()
            self.nyears = np.array([len(set(sr.index.year)) for sr in self.ts]).max()
        else:
            self.mindate = pd.to_datetime('01-01-1950', format='%d-%m-%Y', errors='ignore')
            self.maxdate = pd.Timestamp.today()
            self.nyears  = 0
            

        # if series is empty
        for i,sr in enumerate(ts):
            if len(sr[sr.notnull()])==0:
                self.ts[i] = sr.fillna(0)

        # create figure
        self.fig = plt.figure(facecolor='#eeefff')
        #self.fig = plt.figure(figsize=(9, 8), dpi= 80, facecolor='#eeefff', edgecolor='k')
        #plt.rcParams['figure.figsize'] = [10, 5]

        # create_axes
        create_axes(mps)

        # define legend labels
        lbs = [series.name for series in ts]

        """
        # add filter length to series labels
        if len(lbs)!=0 and len(description)<=len(lbs):
            for i,dfdesc in enumerate(description):
                colindex = description[i].columns.get_loc("filtopcmnap")
                filtop = description[i].iloc[0,colindex]
                colindex = description[i].columns.get_loc("filbotcmnap")
                filbot = description[i].iloc[0,colindex]
                lbs[i] = lbs[i]+" [filter "+filbot+"-"+filtop+" cmnap]"
        """

        # define line colors
        # colors = ['b','r','m','y','c','k','g']
        skytones = ['#172458','#354898','#607cbd','#95b3d7','c','k','g'] # by rehenry
        maximilian = ['#d3d3d3','#e9e9e9','#a6bbca','#86a0b3','#65899d'] # by brynnreacjlocal
        magazine2 = ['#153f79','#79153f','#3f7915','#794f15','#1e1e1e']
        rainbow = ['#2347c5','#b41515','#1c9018','#ecee19','#ce11f2']
        easterpastel = ['#d666c6','#6e64db','#7ad89d','#67a3db','#dfe755']

        # avoid i out of bounds 
        colors = rainbow*10

        # plot all time series
        #ts.reverse()
        #lbs.reverse()
        plt.sca(self.axgws)
        if mps.empty: # geen meetpunt referentiehoogte gegeven
            if len(ts)!=0 and len(lbs)!=0:
                for i,series in enumerate(ts):
                    if len(plotargs)>=i+1:
                        if not 'color' in plotargs[i].keys(): plotargs[i]['color']=colors[i]
                        self.axgws = series.plot(label=lbs[i], **plotargs[i])
                    else:
                        self.axgws = series.plot(color=colors[i],label=lbs[i])
        else:
            # plot only first roundwater series on bottom graph
            self.axgws = ts[0].plot(color=colors[0],label=lbs[0])


        # set axlim
        set_axlim()

        # Set ticklabels for gws graph
        for label in self.axgws.get_xticklabels():
            label.set_color('k')
            label.set_fontsize = 5.0
            label.set_visible(True)
            label.set_rotation(0)
            label.set_horizontalalignment('center')
            
        yticklabels = self.axgws.get_yticklabels()
        for label in yticklabels:
            label.set_color('k')
            label.set_fontsize = 5.0
            label.set_visible(True)

        # plot ylabel for groundwater level graph
        if ylabel:
            plt.ylabel(ylabel, size = 11.0)
        else:
            plt.ylabel('grondwaterstand',size = 11.0)

        # set x-axis title for groundwater level graph off    
        self.axgws.set_xlabel('')

        # settings for mp reference graph
        if not mps.empty:
            reference_graph()

        if len(lbs)!=0:
            plt.legend(shadow = False, loc = 4)
            #print(lbs)
            #plt.legend().get_frame().set_linewidth(0.0)
            self.axgws.legend(loc='lower left', ncol=4, bbox_to_anchor=(0., -0.20, 1., .15), mode="expand", borderaxespad=0.,frameon=False)
            #leg = plt.legend()

        # plot legend texts
        ltext = plt.gca().get_legend().get_texts()
        #print(ltext[0])
        for i in range(len(ltext)):
            plt.setp(ltext[i], fontsize = 9.0, color = 'k')

        # plot title
        if title:
            if mps.empty:
                plt.text(0.0,1.02,title,transform=self.axgws.transAxes)
            else:
                plt.text(0.0,1.1,title,transform=self.axmp.transAxes)

        # plot datespan right of graph
        timespan = self.mindate.strftime("%d-%m-%Y")+" t/m "+self.maxdate.strftime("%d-%m-%Y")

        # right of graph 90 degrees upward
        self.axgws.text(1.03, 0., timespan, horizontalalignment='center',verticalalignment='bottom',rotation='vertical',transform=self.axgws.transAxes)


        return self.fig

    def plotduurlijn(self,frq):
        # Create figure
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot()
        self.fig.hold(True)        

        xas = [0,10,20,30,40,50,60,70,80,90,100]
        for i,year in enumerate(frq):
            #yas = frq.iloc[i].values[0:11]
            colnames = ['0%','10%','20%','30%','40%','50%','60%','70%','80%','90%','100%']
            yas = frq[colnames].iloc[i].values

            #self.ax1 = series.plot(color=colors[i])
            #self.ax1 = 
            plt.plot(xas,yas,'b-')

        # set ax limits
        yrange = plt.gca().get_ylim()
        min = (floor(yrange[0]/10.))*10. # round to decimals
        max = (ceil(yrange[1]/10.))*10.  # round to decimals
        #max = 0

        plt.gca().set_ylim([max,min])
        #plt.yticks(range(200,-50-10,10))

        # grid
        plt.grid(True,which="both",ls="-")

    def saveplot(self,filename):
        # Save figure to file
        #fig = plt.figure(1)
        mydpi = 200.0 # default dpi is 100.0
        #mydpi = self.fig.dpi
        self.fig.set_dpi(mydpi)
        self.fig.set_size_inches(160*mm,80*mm)
        self.fig.savefig(filename,dpi=mydpi, facecolor='w', edgecolor='w', bbox_inches="tight") #additional_artists=self.addart,
        #fig.close()
        #plt.clf() # open straks geen nieuwe plot (dat kost geheugen)
        # show plot
        #plt.show()
        #plt.close()


if __name__ == '__main__':

    def message(message):
        """ function for printing message to screen """
        print()
        print("-"*len(message))
        print(message)
        print("-"*len(message))
        print()

    if 1:

        # test plotseries with two series

        # read data to series

        dn1 = dinogws()
        dn1.readfile(r".\testdata\B34D0081001_1.csv")

        dn2 = dinogws()
        dn2.readfile(r".\testdata\B34D0081002_1.csv")

        sr1 = dn1.series(units="cmnap")
        sr2 = dn2.series(units="cmnap")

        desc1 = dn1.describe()
        desc2 = dn2.describe()

        # test pplotseries : twee meetreeksen
        message("Test plotseries with two series   ")

        #plt.rcParams['figure.figsize'] = [5, 3]

        myplotargs = [
            {'color':'#2347c5', 'marker':'o', 'linestyle':'dashed','linewidth':1, 'markersize':4},
            {'color':'#b41515', 'marker':'o', 'linestyle':'solid', 'linewidth':1, 'markersize':4}]

        plot = plotseries()
        plot.plotseries(ts=[sr1,sr2],description=[desc1,desc2], xlim=[1955,2005], ylim=[1500,1800], title="Test: Twee meetreeksen",
                        plotargs = myplotargs)
        plot.saveplot('.\\output\\test plotseries\\test twee meetreeksen.png')
        plt.show()

    if 0:

        # test plotseries 

        # read data to series

        dn1 = dinogws()
        dn1.readfile(r".\testdata\B12B0297001_1.csv")
        sr1 = dn1.series(units="cmmv")
        desc1 = dn1.describe()

        # test pplotseries : twee meetreeksen
        message("Test plotseries with sbb ref point DRAn-B601a.2   ")

        plot = plotseries()

        plot.plotseries(ts=[sr1],description=[desc1],reference="cmmv",xlim=['01-01-1997','14-11-1999'],
            ylim=[-50,200], title="Test: SBBRefpunt DRAn-601a.2")
        plot.saveplot('.\\output\\test plotseries\\test-sbbref.png')
        plt.show()

    if 0:

        # test plotseries : één reeks met referentielijn
        message("Test plotseries with reference line   ")

        ref = dn1.mpref()
        plot = plotseries()
        plot.plotseries(ts=[sr1],description=[desc1], title="Test: Meetreeks met referentielijn", mps=ref)
        plot.saveplot('.\\output\\test plotseries\\test meetreeks-met-referentie.png')
        plt.show()


    if 0: # test plotduurlijn
        if dn1.frq(): plot.plotduurlijn(dn1.frq)
        plot.saveplot('duurlijn.png')
        plt.show()

    if 0: # test plot series with interesting reference series

        plot = plotseries()    
        dn = dinogws()
        #dn.readfile(r".\testdata\B28A0475001_1.csv")
        dn.readfile(r".\testdata\B29C0191001_1.csv")

        if len(dn.series())!=0:
            sr = dn.series(units="cmnap")
            ref = dn.mpref()
            desc = dn.describe()
            mytitle = "Test: plot B29C0191 with interesting reference line"
            plot.plotseries(ts=[sr],reference="cmnap",description=[desc],mps=ref,title=mytitle)
            plot.saveplot('meetreeks-met-referentie.png')
            plt.show()

    if 0: 
        if dn.frq(): 
            plot.plotduurlijn(dn.frq)
            plot.saveplot('duurlijn.png')
            plt.show()        


    if 0: # test functions for all files in directory with test files (with many problems)

        sourcedir = ".\\testdata\\"           
        filenames = [f for f in os.listdir(sourcedir) if os.path.isfile(os.path.join(sourcedir,f)) and f[11:13]=="_1"]
        for i,srcfile in enumerate(filenames):

            dn = dinogws(sourcedir+srcfile)
            plot = plotseries()
            #dn.readfile(sourcedir+srcfile)
            if len(dn.series())!=0:
                sr = dn.series(units="cmnap")
                ref = dn.mpref()
                plot.plotseries(ts=[sr],mps=ref, title=srcfile)
                plot.saveplot(".\\output\\log\\graph\\"+srcfile.split(".")[0]+".png")
                plt.show()
                plt.close()

    print ("Script finished")

