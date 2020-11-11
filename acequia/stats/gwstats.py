
"""
Object for calculating statistics from one groundwater series

History: Created as clsGwStats.py on 16-08-2015, last updated 12-02-1016
         Migrated to acequia on 15-06-2019

@author: Thomas de Meij

"""

import os
import os.path
from datetime import datetime
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import xlsxwriter
#from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell

#import acequia as aq

##import clsDINOGWS
##reload(clsDINOGWS)
##from clsDINOGWS import dinogws

class GwStats:
    """Calculate statistics from a (groundwater)series"""

    statscols = [
        'series','hydrojaar','n','n14','gem','hg3','lg3','vg3','vg1apr',
        'wrnfrq']

    sumstatscols = [
        'series','nyears','n14avg','maxfrq','nmax','status','years',
        'gwsavg','ghgavg','glgavg','gvg3avg','gvg1apravg','gwsstd',
        'ghgstd','glgstd','gvg3std','gvg1aprstd','gwsse','ghgse',
        'glgse','gvg3se','gvg1aprse','gvg-vds82','gvg-run89','ghgw',
        'glgz','gvg-vds89pol','gvg-vds89str']

    gvgdiffcols = [
        'series','nyears','gvg1apravg','gvg3avg','gvg-vds82',
        'gvg-run89','gvg-vds89pol','gvg-vds89str']


    N14 = 26 # Years with max 26 measurement are considered 14 day measurements
    maxdays = 7 # use estimate for value on a day only when measurement is taken less than maxdays from that date
    minN14 = 19 # mininmal number of values in a year for valid N14 series
    actyears = 5 # number of years for status actueel/historisch


    def __repr__(self):
        return "Calculate statistics for a (groundwater)series"


    def __init__(self, series=Series(), ref=None):





        self.reset()
        if not series.empty: 
            self.setseries(series,ref=ref)

    def reset(self):
        """ Reset all variables """


        # create list of frequency column names
        self.qt = np.linspace(0,1,11) # list of quantiles
        self.qtnames = ["p"+str(int(x*100)) for x in self.qt]
        self.frqcols = ["series","hydrojaar","n"]+self.qtnames

        # create empty dataframes
        self.sr = Series() 
        self.dfdata = DataFrame()
        self.sr14 = Series()
        self.dfdata14 = DataFrame()
        self.dfstats = DataFrame(columns=self.statscols)        
        self.dfsumstats = DataFrame(columns=self.sumstatscols)
        self.dfgvgdiff =  DataFrame(columns=self.gvgdiffcols)
        self.dffrq = DataFrame(columns=self.frqcols)


    def setseries(self,sr,quantiles=False,stats=False,seriesname=None,ref=None):
        """ set values of series with groundwater data """
        
        # reset variables
        self.reset()
        self.sr = sr
        
        # set series name
        if seriesname!=None: sr.name=seriesname
        elif len(sr.name)!=0: self.sr.name = sr.name
        else: sr.name="reeksnaam"
        
        # set reference
        if ref == None: self.reference = "cmnap"
        elif ref == "cmnap":self.reference = "cmnap"
        elif ref == "cmmv": self.reference = "cmmv"
        elif ref == "cmmp": self.reference = "cmmp"
        else:
            self.reference = ref
            print(sr.name," has invalid reference ",self.reference)
        
        
        # if timeseries not empty:
        if len(self.sr[self.sr.notnull()])!=0:
        
            # calculate hydrological years from dates and make dataframe
            hydrojaar = np.where(self.sr.index.month<4,self.sr.index.year-1,self.sr.index.year)
            seizoen = np.where((self.sr.index.month>3) & (self.sr.index.month<10),"zomer","winter")
            self.dfdata = DataFrame({"data":self.sr.values,"hydrojaar":hydrojaar,"seizoen":seizoen},index=self.sr.index)
            
            # make 14day values series and save hydroyears to dataframe
            self.sr14 = self.series14()
            hydrojaar = np.where(self.sr14.index.month<4,self.sr14.index.year-1,self.sr14.index.year)
            seizoen = np.where((self.sr14.index.month>3) & (self.sr14.index.month<10),"zomer","winter")
            self.dfdata14 = DataFrame({"data":self.sr14.values,"hydrojaar":hydrojaar,"seizoen":seizoen},index=self.sr14.index)

            # calculate statistics
            if quantiles: self.quantiles()
            if stats: self.stats()
            
        return self.dfdata,self.dfdata14
        
    def series(self):
        """ return original groundwater series as pandas series """
        return self.sr
 
    """
    def series14(self):
        """ #return 14daagse meetreeks as pandas timeseries 
        """        
        if self.sr14.empty and len(self.dfdata)>0:
            # Create timeseries with 14day values
            grp = self.dfdata.groupby(self.dfdata["hydrojaar"]) # create group object

            # self.N = timeseries with number of measurements for each hydrological year
            N = grp["data"].count() #.to_frame(name="N")# calculate number of measurements

            # selecteer meetgegevens uit hydrologische jaren met veertiendaagse waarnemingen (of minder)
            lofrqyears = N[N<=self.N14].index
            self.sr14 = self.dfdata[self.dfdata["hydrojaar"].isin(lofrqyears)]["data"]            
            ##self.dfdata14 = self.dfdata[self.dfdata["hydrojaar"].isin(lofrqyears)]

            # create 14daagse data voor alle jaren met hoogfrequente waarnemingen            
            hifrqyears = N[N>self.N14].index
            datestrings14 = [str(day)+"-"+str(month)+"-"+str(year) for year in hifrqyears for month in list(range(1,13)) for day in [14,28]]
            datetimes14 = pd.to_datetime(datestrings14) # dates to select from original timeseries to get 14day values for high frequency years
            sr14 = self.dfdata[self.dfdata.index.isin(datetimes14)]

            # append hifrq selection to self.sr14
            self.sr14 = self.sr14.append(sr14["data"])

            # set name sr14
            self.sr14.name = self.sr.name
        #elif s:
        #    self.sr14 = Series()
        return self.sr14
    """

    def quantiles(self):
        """ Return dataframe with quantiles for ech hydrological year 
        """
        
        if self.dffrq.empty:

            # fill columns with data
            if len(self.dfdata)>0:
    
                # create group object
                grp = self.dfdata.groupby(self.dfdata["hydrojaar"])
                
                # expand dffrq with index hydrojaar
                allyears = np.arange(self.dfdata["hydrojaar"].min(),self.dfdata["hydrojaar"].max()+1)
                self.dffrq = self.dffrq.reindex(index=allyears)

                # create dataframe with frequencies
                if not self.dffrq.empty:
                    # fill columns series, hydrojaar and n
                    self.dffrq["series"]=self.sr.name
                    self.dffrq["hydrojaar"]=self.dffrq.index
                    self.dffrq["n"]=grp.count()

                    for i,(qtname,qtval) in enumerate(zip(self.qtnames,self.qt)):
                        self.dffrq[qtname] = grp["data"].quantile(qtval) #.round(0)

                    # reindex dffrq
                    self.dffrq = self.dffrq.reset_index(drop=True,inplace=False)
                    
                    # round numbers
                    for col in self.dffrq:
                        if self.dffrq[col].dtype=="float64": self.dffrq[col] = round(self.dffrq[col])

                else: # return empty dataframe when no data are available
                    colnames = ["series","hydrojaar","n"]+self.qtnames
                    self.dffrq = DataFrame(columns = colnames)
        return self.dffrq

    def stats(self):
        """ Return pandas dataframe with statistics for each hydrological year """

        def frqclass(freq):
            """ Determine frequency class from number of measurements n """
            if freq>27: frqcls = "dag"
            elif freq>12: frqcls = "14dagen"
            elif freq>9: frqcls = "maand"
            else: frqcls = "zelden"
            return frqcls


        ## create empty dataframes with columns           
        ##if self.dfstats.empty: self.dfstats=DataFrame(columns=self.statscols)
        ##if self.dfsumstats.empty: self.dfsumstats=DataFrame(columns=self.sumstatscols)
        ##if self.dfgvgdiff.empty: self.dfgvgdiff=DataFrame(columns=self.gvgdiffcols)

        # fill dfstats and dfsumstats with statistics
        n14count = len(self.sr14[self.sr14.notnull()])
        if n14count!=0 and self.dfstats.empty: # and self.dfsumstats.empty:

            # --------------------------------------------------------------------------------
            # calculate gvg directly from measurements
            # --------------------------------------------------------------------------------
            # create table self.dfvg with lots of values needed for calculation the VG and GVG
            # use two calculation methodes: 
            # first:  the average of 14mrt, 28mrt and 14 april (this is the vg3)
            # second: the value nearest to 1apr (this is the vg1apr)

            # calculate vg3 based on the average of three measurements for each calender year
            # de drie te middelen datums zijn : 14 maart, 28 maart en 14 april
            # toelichting op de variabelen:
            #  yeargrp     : vg3 is gebaseerd op groepen per kalenderjaar van de feitelijke meetreeks 
            #  vgindex     : lijst van rangnummers van de waarneming het dichtste bij de aangegeven datum voor ieder kalenderjaar 
            #  vg          : grondwaterstand op aangegeven datum voor ieder kalenderjaar
            #  vgdagen     : aantal dagen tussen de gekozen datum van de gemeten voorjaarsgrondwaterstand en 1 april
            vgdatums = [{"label":"14mrt","dag":14,"maand":3},{"label":"28mrt","dag":28,"maand":3},{"label":"14apr","dag":14,"maand":4}]            
            for i,datum in enumerate(vgdatums):
                yeargrp = self.dfdata["data"].groupby(self.dfdata.index.year)
                ##vgindex = yeargrp.apply(lambda x: np.argmin([abs(x.index[i].to_datetime()-datetime(x.index[i].year,datum["maand"],datum["dag"])) for i in range(len(x))]))
                vgindex = yeargrp.apply(lambda x: np.argmin([abs(x.index[i].to_pydatetime()-datetime(x.index[i].year,datum["maand"],datum["dag"])) for i in range(len(x))]))
                vg = yeargrp.apply(lambda x:x[vgindex.loc[x.index[0].year]])
                ##vgdagen = yeargrp.apply(lambda x: sorted([abs(x.index[i].to_datetime()-datetime(x.index[i].year,datum["maand"],datum["dag"])) for i in range(len(x))])[0])
                vgdagen = yeargrp.apply(lambda x: sorted([abs(x.index[i].to_pydatetime()-datetime(x.index[i].year,datum["maand"],datum["dag"])) for i in range(len(x))])[0])
                vgdagen = Series(vgdagen.dt.days.values,index=vg.index)
                
                if i==0: self.dfvg = DataFrame(index=vg.index)
                self.dfvg["vg"+datum["label"]]=vg
                self.dfvg[datum["label"]+"dagen"]=vgdagen

            # Calculate vg1apr : grondwaterstand op 1 april
            # toelichting op de variabelen:
            #  yeargrp     : gvg is gebaseerd op groepen per kalanderjaar van de feitelijke meetreeks 
            #  gvgindex    : lijst van rangnummers van de waarneming het dichtste bij 1 april voor ieder kalenderjaar 
            #  vg1apr      : grondwaterstand op 1 april voor ieder kalenderjaar
            #  vg1aprdagen : aantal dagen tussen de gekozen datum van de gemeten voorjaarsgrondwaterstand en 1 april
            yeargrp = self.dfdata["data"].groupby(self.dfdata.index.year)
            ##vg1aprindex = yeargrp.apply(lambda x: np.argmin([abs(x.index[i].to_datetime()-datetime(x.index[i].year,4,1)) for i in range(len(x))]))
            vg1aprindex = yeargrp.apply(lambda x: np.argmin([abs(x.index[i].to_pydatetime()-datetime(x.index[i].year,4,1)) for i in range(len(x))]))
            self.dfvg["vg1apr"] = yeargrp.apply(lambda x:x[vg1aprindex.loc[x.index[0].year]])
            ##self.dfvg["vg1aprdagen"] = yeargrp.apply(lambda x: sorted([abs(x.index[i].to_datetime()-datetime(x.index[i].year,4,1)) for i in range(len(x))])[0])
            self.dfvg["vg1aprdagen"] = yeargrp.apply(lambda x: sorted([abs(x.index[i].to_pydatetime()-datetime(x.index[i].year,4,1)) for i in range(len(x))])[0])
            self.dfvg["vg1aprdagen"] = self.dfvg["vg1aprdagen"].dt.days.values

            # clean up dfvg table : nan values when actual date of measurement is more than maxdays away from given date
            for date,dgn in [["vg14mrt","14mrtdagen"],["vg28mrt","28mrtdagen"],["vg14apr","14aprdagen"],["vg1apr","vg1aprdagen"]]:
                bool = self.dfvg[dgn]<self.maxdays
                dateval = self.dfvg[date].values
                self.dfvg[date] = np.where(bool,dateval,np.nan)
                ## geen idee waarom regels hieronder geprogrammeerd zijn:
                ## format number of days (of timedelta type) as just a number type:
                ## oud: geeft fout: self.dfvg[date] = self.dfvg[date].apply(lambda x:x.astype('timedelta64[D]')/np.timedelta64(1,'D'))
                ## self.dfvg[date] = self.dfvg[date].apply(lambda x:pd.Timedelta(x,unit='d')/pd.Timedelta(1,unit='d'))

            # calculate vg3 for each year as the average of three columns
            self.tmp = self.dfvg[["vg14mrt", "vg28mrt","vg14apr"]]
            self.dfvg["vg3"]=self.dfvg[["vg14mrt", "vg28mrt","vg14apr"]].mean(axis=1).round(0)           

            # -------------------------------------------------------------------
            # create table self.dfstats with all statistics n, n14, hg3, lg3, etc
            # -------------------------------------------------------------------            

            # create group object grouped on hydroyear
            grp = self.dfdata.groupby(self.dfdata["hydrojaar"])

            # expand empty dataframe dfstats to length number of groups
            # index of grp is "hydroyear"
            rowindex = [name for name,group in grp]
            self.dfstats.reindex(rowindex)

            # calculate n measurements and average grondwater level for each hydrological year for orgiginal series
            self.dfstats["n"] = grp["data"].count()
            self.dfstats["gem"] = grp["data"].mean().round(0)

            # create group object for 14day values series
            grp14 = self.dfdata14.groupby(self.dfdata14["hydrojaar"])

            # calculate hg3, lg3
            if self.reference == "cmmv" or self.reference == "cmmp":
                self.hg3 = grp14["data"].apply(lambda x: x.sort_values(ascending=True).values[:3].mean().round(0))
                self.lg3 = grp14["data"].apply(lambda x: x.sort_values(ascending=False).values[:3].mean().round(0))
            elif self.reference == "cmnap":
                self.hg3 = grp14["data"].apply(lambda x: x.sort_values(ascending=False).values[:3].mean().round(0))
                self.lg3 = grp14["data"].apply(lambda x: x.sort_values(ascending=True).values[:3].mean().round(0))
            else:
                self.hg3 = np.nan
                self.lg3 == np.nan

            # -------------------------------------------------------------------------
            # calculate HG3 from winter and LG3 from summer according to Van der Sluijs
            # -------------------------------------------------------------------------      

            # calculate hg3 for each winter based on hydrological year from 14day values
            grp = self.dfdata14[self.dfdata14.seizoen=="winter"].groupby("hydrojaar")
            if self.reference == "cmmv" or self.reference == "cmmp":
                self.hg3w = grp["data"].apply(lambda x: x.sort_values(ascending=True).values[:3].mean().round(0))
            elif self.reference == "cmnap":
                self.hg3w = grp["data"].apply(lambda x: x.sort_values(ascending=False).values[:3].mean().round(0))
            else:
                self.hg3w = np.nan

            # calculate lg3 for each summer based on hydrological year from 14day values                    
            grp = self.dfdata14[self.dfdata14.seizoen=="zomer"].groupby("hydrojaar")
            if self.reference == "cmmv" or self.reference == "cmmp":
                self.lg3z = grp["data"].apply(lambda x: x.sort_values(ascending=False).values[:3].mean().round(0))
            elif self.reference == "cmnap":
                self.lg3z = grp["data"].apply(lambda x: x.sort_values(ascending=True).values[:3].mean().round(0))
            else:
                self.lg3z == np.nan

            # -------------------------------------------------------------------
            # add cokumns to dfstats
            # -------------------------------------------------------------------            

            # add columns to dfstats
            self.dfstats["n14"] = grp14["data"].count()
            self.dfstats["hg3"] = self.hg3
            self.dfstats["lg3"] = self.lg3
            self.dfstats["vg3"] = self.dfvg["vg3"]
            self.dfstats["vg1apr"] = self.dfvg["vg1apr"]
            self.dfstats["hg3w"] = self.hg3w
            self.dfstats["lg3z"] = self.lg3z

            # calculate observation frequancy for each hydrological year
            self.dfstats["wrnfrq"] = self.dfstats["n"].apply(lambda x:frqclass(x))

            # voeg eventueel ontbrekende jaren in met NaN waarden voor frequenties
            allyears = np.arange(min(self.dfstats.index),max(self.dfstats.index)+1)
            self.dfstats = self.dfstats.reindex(index=allyears)

            # fill column series
            self.dfstats["series"] = self.sr.name

            # add index values to column hydrojaar and reset index
            self.dfstats["hydrojaar"] = self.dfstats.index
            self.dfstats = self.dfstats.reset_index(drop=True,inplace=False)

            ##reorder columns
            ##self.statscols = ['series','hydrojaar','n','n14','gem','hg3','lg3','vg3','vg1apr','wrnfrq']
            ##colnames = self.statscols + [colname for colname in list(self.dfstats) if colname not in self.statscols]
            ##self.dfstats = self.dfstats[colnames].copy()

            # -----------------------
            # create table dfsumstats
            # -----------------------

            # select year with enough measurements
            self.valyears = self.dfstats[self.dfstats["n14"]>=self.minN14]

            # calculate averages over available years 
            rec = dict()
            rec["series"] = self.sr.name
            rec["nyears"] = len(self.valyears)
            rec["nmax"] = self.valyears.n.max()
            rec["n14avg"] = self.valyears.n14.mean()
            rec["gwsavg"] = self.valyears.gem.mean()

            # calculate GHG, GLG and GVG
            rec["ghgavg"] = self.valyears.hg3.mean()
            rec["glgavg"] = self.valyears.lg3.mean()
            rec["gvg3avg"] = self.valyears.vg3.mean()
            rec["gvg1apravg"] = self.valyears.vg1apr.mean()

            # calculate standard deviations
            rec["gwsstd"] = self.valyears.gem.std()            
            rec["ghgstd"] = self.valyears.hg3.std()
            rec["glgstd"] = self.valyears.lg3.std()
            rec["gvg3std"] = self.valyears.vg3.std()
            rec["gvg1aprstd"] = self.valyears.vg1apr.std()

            # calculate standard errors
            rec["gwsse"] = self.valyears.gem.std()/np.sqrt(len(self.valyears))
            rec["ghgse"] = self.valyears.hg3.std()/np.sqrt(len(self.valyears))
            rec["glgse"] = self.valyears.lg3.std()/np.sqrt(len(self.valyears))
            rec["gvg3se"] = self.valyears.vg3.std()/np.sqrt(len(self.valyears))
            rec["gvg1aprse"] = self.valyears.vg1apr.std()/np.sqrt(len(self.valyears))

            rec["ghgw"] = self.valyears.hg3w.mean()
            rec["glgz"] = self.valyears.lg3z.mean()

            # calculate GVG with the Van der Sluijs (1982) formula
            # and Runhaar (1989) formula based on hydrological year
            GHG = rec["ghgavg"]
            GLG = rec["glgavg"]
            if self.reference=="cmmv": 
                rec["gvg-vds82"] = np.round(5.4 + 1.02*GHG + 0.19*(GLG-GHG))
                rec["gvg-run89"] = np.round(0.5 + 0.85*GHG + 0.20*GLG) # (+/-7,5cm)
            else: 
                rec["gvg-vds82"] = np.nan
                rec["gvg-run89"] = np.nan

            # calculate GVG with the Van der Sluijs (1989) formula
            # based on summer and winter
            GHG = rec["ghgw"]
            GLG = rec["glgz"]
            if self.reference=="cmmv":
                rec["gvg-vds89pol"] = np.round(12.0 + 0.96*GHG + 0.17*(GLG-GHG))
                rec["gvg-vds89str"] = np.round(4.0 + 0.97*GHG + 0.15*(GLG-GHG))
            else:
                rec["gvg-vds89pol"] = np.nan
                rec["gvg-vds89str"] = np.nan

            # determine maximum observation frequency of series
            if np.any(self.valyears.wrnfrq.values=="dag"): rec["maxfrq"]="dag"
            elif np.any(self.valyears.wrnfrq.values=="14dagen"): rec["maxfrq"]="14dagen"
            elif np.any(self.valyears.wrnfrq.values=="maand"): rec["maxfrq"]="maand"
            else: rec["maxfrq"]="zelden"

            # calculate series status
            lastyear = self.sr.index.year.values[-1]
            if lastyear < datetime.now().year - self.actyears:
                rec["status"] = "historisch"
            else:
                rec["status"] = "actueel"

            # join all available years in one string
            rec["years"] = " ".join([str(year) for year in self.valyears.hydrojaar])

            # create dataframe from rec
            self.rec=rec
            self.dfsumstats = DataFrame([rec],columns=self.sumstatscols)

            # calculate differences
            if self.reference=="cmmv":
                refcol = "gvg1apravg"
                self.dfgvgdiff = self.dfsumstats[self.gvgdiffcols].copy()
                for col in self.gvgdiffcols:
                    if col not in ["series","nyears","status","gvg1apravg"]:
                        colname = col+"-diff"
                        self.dfgvgdiff[colname] = (self.dfgvgdiff[refcol]-self.dfgvgdiff[col]).round(0)

        return self.dfstats,self.dfsumstats,self.dfgvgdiff,self.sr,self.sr14

    def tables(self):
        """ return table with series name, hydrological year and percentiles
            meant for addition to a large csv file"""

        # make sure stats are available
        dfstats,dfsumstats,dfgvgdiff,sr,sr14 = self.stats()        

        """
        # create dfg3tbl
        if not dfstats.empty:
            # create nice table from dfstats with series name for export to csv file
            # copy dffrq (and lose index with years)
            dfg3tbl = dfstats.reset_index(drop=True,inplace=False)
            labels = [sr.name for row in range(len(dfg3tbl))]
            dfg3tbl.insert(0,'reeksnaam',labels)
            dfg3tbl.insert(1,'hydrojaar',dfstats.index)            
        else:
            cols = ["reeksnaam"]+list(dfstats)
            dfg3tbl = DataFrame(columns=cols)

        # create dfgxg
        if not dfsumstats.empty:                
            dfgxg = dfsumstats.reset_index(drop=True,inplace=False)
            labels = [sr.name for row in range(len(dfgxg))]
            dfgxg.insert(0,'reeksnaam',labels)
        else:
            dfgxg = DataFrame()
        """
        dfg3tbl = dfstats.copy()
        dfgxg = dfsumstats.copy()
        dfgvgdiff = dfgvgdiff.copy()

        return dfg3tbl,dfgxg,dfgvgdiff

        
    def to_excel_fast(self,filename):
        """ Save series and all statistics  to excel file """
        
        def add_totals(sheet,df,colnumbers):
            """ Add total formulas to worksheet """

            number_rows = len(df.index)          
            for icol in colnumbers:

                # define formula range
                start_range = xl_rowcol_to_cell(1, icol)

                end_range = xl_rowcol_to_cell(number_rows,icol)
                
                # write column name                
                colname_location = xl_rowcol_to_cell(number_rows+2,icol)
                col_name = list(df)[icol]
                ws.write_string(colname_location,col_name,label_fmt)

                # write formulas
                frm_list = [("COUNT","nyear"),("MIN","min"),("MAX","max"),("MEDIAN","med"),("AVERAGE","gem"),{"STDEV","stdev"}]
                for irow,(formname,description) in enumerate(frm_list):

                    formula = "=" + formname + "({:s}:{:s})".format(start_range, end_range)
                    label_location = xl_rowcol_to_cell(number_rows+irow+3,1)
                    cell_location = xl_rowcol_to_cell(number_rows+irow+3,icol)

                    # write values to excel

                    ws.write_string(label_location, description, label_fmt)
                    ws.write_formula(cell_location, formula, total_fmt)
            return ws

        # create excel writer
        writer = pd.ExcelWriter(filename,
                                datetime_format='dd-mm-yyyy',
                                date_format="dd-mm-yyyy") #datetime_format='dd mm yyyy hh:mm:ss'

        # get statistics
        dfstat,dfsumstat,dfgvgdiff,ts,ts14 = self.stats()
        dfqt = self.quantiles()

        # format dataframes and write to excel
        for df,sheetname in [(dfstat,"stats"),(dfqt,"frq"),(dfsumstat,"summary"),(dfgvgdiff,"dfgvgdiff")]:       

            # round numbers
            for col in df:
                if df[col].dtype=="float64":
                    df[col] = round(df[col])

            # write to excel
            df.to_excel(writer,sheetname,index=False)

        # add totals
        wb = writer.book
        
        # define formats
        total_fmt = wb.add_format({'align': 'right', 'num_format': '#,##0','bold': False, 'bottom':0})
        label_fmt = wb.add_format({'align': 'right'})

        # add totals 
        ws = writer.sheets["stats"]
        colnrs = [2,3,4,5,6,7,8]
        ws = add_totals(ws,dfstat,colnrs)

        ws = writer.sheets["frq"]
        colnrs = [2,3,4,5,6,7,8,9,10,11,12,13]
        ws = add_totals(ws,dfqt,colnrs)        
        
        # write series to excel
        tscopy = ts.copy()
        tscopy.name="standen"
        #df = DataFrame(data={"datum":ts.index.to_datetime(dayfirst=True),"standen":ts.values})
        DataFrame(tscopy).to_excel(writer,'meetreeks') #,index=False)
        writer.sheets["meetreeks"].set_column('A:A', 18)

        # write series14 to excel
        ts14copy = ts14.copy()
        ts14copy.name="standen"
        DataFrame(ts14copy).to_excel(writer,'14daags')
        writer.sheets["14daags"].set_column('A:A', 18)
        
        # save excel file
        writer.save()

        return writer
    
    """
    TO DO: rewrite this function and make it work
    def to_excel(self,filename):
        # Save series and all statistics  to excel file
        
        def convert(value):
            try:
                value/10
            except:
                return str(value)
            else:
                if np.isnan(value):
                    return ""
                else:
                    return round(float(value))

        # get statistics
        self.dfstat,self.dfsumstat,self.dfgvgdiff,self.ts,self.ts14 = self.stats()
        self.dfqt = self.quantiles()

        # create workbook
        self.wb = xlsxwriter.Workbook(filename)
        ##self.ws = self.wb.active
        
        # write dfstat
        self.ws = self.wb.add_worksheet('stats')
        #self.ws.title = "statistieken"
        self.ws.append(list(dfstat))
        colnames = list(self.dfstat)
        for i in range(len(self.dfstat)):
            #for i in range(len(colnames)):
            row = [convert(self.dfstat.iloc[i,j]) for j in range(len(colnames))]
            self.ws.append(row)

        # markup dfstat
        for row in self.ws.iter_rows():
            for cell in row:
                cell.alignment = oxl.styles.Alignment(horizontal='left')

        # write dfqt
        self.ws = self.wb.add_worksheet('freq')
        #self.ws.title = "frequenties"
        self.ws.append(list(dfqt))
        colnames = list(self.dfqt)
        for i in range(len(self.dfqt)):
            row = [convert(self.dfqt.iloc[i,j]) for j in range(len(colnames))]
            self.ws.append(row)

        # markup dfgt
        for row in self.ws.iter_rows():
            for cell in row:
                cell.alignment = oxl.styles.Alignment(horizontal='left')

        # write sumstat
        self.ws = self.wb.add_worksheet('sumstat')
        #self.ws.title = "summary"
        if not self.dfsumstat.empty:
            colnames = list(self.dfsumstat)
            for i in range(len(colnames)):
                if colnames[i] in ["years","maxfrq"]:
                    self.ws.append([colnames[i],str(self.dfsumstat.iloc[0,i])])
                #elif colnames[i] in ["nyears"]:
                else:
                    self.ws.append([colnames[i],convert(self.dfsumstat.iloc[0,i])])
        else:
            colnames = list(self.dfsumstat)
            for i in range(len(colnames)):
                self.ws.append([colnames[i]])

        # markup sumstat
        for row in self.ws.iter_rows():
            for cell in row:
                cell.alignment = oxl.styles.Alignment(horizontal='left')

        # write gvgdiff
        self.ws = self.wb.create_sheet('gvgdiff')
        #self.ws.title = "gvgdiff"
        colnames = list(self.dfgvgdiff)
        for i in range(len(colnames)):
            if colnames[i] in ["years","maxfrq"]:
                self.ws.append([colnames[i],str(self.dfsumstat.iloc[0,i])])
            #elif colnames[i] in ["nyears"]:
            else:
                if not self.dfsumstat.empty:
                    self.ws.append([colnames[i],convert(self.dfsumstat.iloc[0,i])])
                else:
                    self.ws.append([colnames[i]])

        # write series14
        self.ws = self.wb.add_worksheet('14daags')
        #self.ws.title = "14daags"
        self.ws.append(["datum","stand"])
        dates  = self.ts14.index.date
        for i in range(len(dates)):
            if not np.isnan(self.ts14.iloc[i]):
                self.ws.append([dates[i],self.ts14.iloc[i]])
            else:
                self.ws.append([dates[i]])  

        # markup series14
        for colname in ['A','B']:
            self.ws.column_dimensions[colname].width = 15
        for cellname in ['A1','B1']:
            self.ws.cell(cellname).alignment = oxl.styles.Alignment(horizontal='right')

        # write series
        self.ws = self.wb.add_worksheet('meetreeks')
        #self.ws.title = "meetreeks"
        self.ws.append(["datum","stand"])
        dates  = self.ts.index.date
        for i in range(len(dates)):
            #print(i,ts
            if not np.isnan(self.ts.iloc[i]):
                self.ws.append([dates[i],self.ts.iloc[i]])
            else:
                self.ws.append([dates[i],""])

        # markup series
        #writer.sheets['Summary'].
        for colname in ['A','B']:
            self.ws.column_dimensions[colname].width = 15
        for cellname in ['A1','B1']:
            self.ws.cell(cellname).alignment = oxl.styles.Alignment(horizontal='right')

        # save workbook and return
        self.wb.save(filename)
        return self.wb
    """

