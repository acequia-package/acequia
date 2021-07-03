""" Read groundwater measurement data from dinoloket csv files.

  Author : Thomas de Meij, 2020
  
  History: 02-02-2014 created for python2.7;
           15-08-2015 migrated to python3.x;     
           06-07-2019 migrated to acequia 

"""

import os
import os.path
from datetime import datetime
import csv
import time
import datetime as dt
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

sep = ","

def read_dinogws():
    """ read data from Dinoloket csv file with groundwater measurement 
    data """
    pass


class DinoGws:
    """Read TNO Dinoloket csv file with groundwater measurement data"""


    _metatag = ','.join(
        ['Locatie','Filternummer','Externe aanduiding',
         'X-coordinaat','Y-coordinaat','Maaiveld (cm t.o.v. NAP)',
         'Datum maaiveld gemeten','Startdatum','Einddatum',
         'Meetpunt (cm t.o.v. NAP)','Meetpunt (cm t.o.v. MV)',
         'Bovenkant filter (cm t.o.v. NAP)',
         'Onderkant filter (cm t.o.v. NAP)'
        ])

    _datatag = ','.join(
        ['Locatie','Filternummer','Peildatum',
         'Stand (cm t.o.v. MP)','Stand (cm t.o.v. MV)',
         'Stand (cm t.o.v. NAP)','Bijzonderheid,Opmerking','','',''
         ])

    _missingdata = (f'Van deze put zijn geen standen opgenomen',
         f'in de DINO-database')

    _header_cols = ["nitgcode","filter","tnocode","xcoor",
        "ycoor","mvcmnap","mvdatum","startdatum","einddatum",
        "mpcmnap","mpcmmv","filtopcmnap","filbotcmnap"]

    _data_cols = ["nitgcode","filter","peildatum","standcmmp",
        "standcmmv","standcmnap","bijzonderheid","opmerking"]

    _head_cols = ['peildatum','standcmmp','bijzonderheid','opmerking']


    def __repr__(self):
        return (f'{self.srname()} (n={len(self._data)})')

    def __init__(self,filepath=None,readall=True):

        # lines marking data blocks in dinofiles

        if isinstance(readall,bool):
            self.readall=readall
        else:
            self.readall=True
            wrnstr = 'Variable \'{vname}\' not of type boolean' \
                     'of type \'{tname}\'. Data wil be read.'.format(
                     vname=readall,tname=type(readall))
            warnings.warn(warnstr)


        # herekenningsregels dinofiles
        self._metatag = "Locatie,Filternummer,Externe aanduiding,X-coordinaat,Y-coordinaat,Maaiveld (cm t.o.v. NAP),Datum maaiveld gemeten,Startdatum,Einddatum,Meetpunt (cm t.o.v. NAP),Meetpunt (cm t.o.v. MV),Bovenkant filter (cm t.o.v. NAP),Onderkant filter (cm t.o.v. NAP)"
        self._datatag = "Locatie,Filternummer,Peildatum,Stand (cm t.o.v. MP),Stand (cm t.o.v. MV),Stand (cm t.o.v. NAP),Bijzonderheid,Opmerking,,,"
        self._missingdata = "Van deze put zijn geen standen opgenomen in de DINO-database"
        self._header_cols = ["nitgcode","filter","tnocode","xcoor","ycoor","mvcmnap","mvdatum","startdatum","einddatum","mpcmnap","mpcmmv","filtopcmnap","filbotcmnap"]
        self._data_cols = ["nitgcode","filter","peildatum","standcmmp","standcmmv","standcmnap","bijzonderheid","opmerking"]

        # create empty variables
        self._reset()
        
        if filepath != None:
            self.flines = self._readfile(filepath)
            self._header, self._data = self._readlines()

        if self._header.empty and not self._data.empty:
            self._header = DataFrame(data=[[np.nan]*len(self._header_cols)],columns=self._header_cols)
            self._header = self._header.astype({'nitgcode':str,'filter':str})
            self._header.at[0,'nitgcode'] = self._data.at[0,'nitgcode']
            self._header.at[0,'filter'] = self._data.at[0,'filter']
            self._header.at[0,'startdatum'] = self._data.at[0,'peildatum']
            #self._tubeprops.at[0,'startdate'] = heads.index[0]


    def _reset(self):
        """ Reset all variables """
        self.filepath = ""
        self.errors = []
        self._data = DataFrame()
        self._header = DataFrame()       
        self._datatext = DataFrame()
        self._headertext = DataFrame()
        self.dfdesc = DataFrame()
        self.dfdescloc = DataFrame()
        self.seriesname = ""

    def _readfile(self,filepath):
        """ Open DINO csv file and return list of filelines """

        self._reset()
        self.filepath = filepath

        try:
            self.file = open(self.filepath,'r')
        except (IOError, TypeError) as err:
            errno, strerror = err.args
            print("{!s}".format(errno), end="")
            print("I/O fout{!s}".format(strerror), end="")
            print (" : "+self.filepath)
            self.errors.append(
                    [self.filepath,
                     "File can not be opened"])
            self.flines=[]
            raise
        else:
            self.flines = self.file.readlines()
            self.file.close()

        return self.flines


    def _readlines(self):
        """ read list of file lines from dinofile to data """

        # assert file is valid ascii
        if len(self.flines)==0:
            file_valid = False
        elif self.flines[0][0]=='\x00':
            # test for corrupted file with only 'x00' 
            # Yes, I have really seen this
            file_valid=False
        else:
            file_valid = True

        if file_valid==False:
            self.headerstart=0
            self.headerend=0
            self.datastart=0
        else:
            # findlines in dinofile lines
            self.headerstart, self.headerend, self.datastart = \
                self._findlines()
        
        # read header
        if self.headerstart>0 and self.headerend>0: 
            self._header = self._readheader()
        else:
            self._header = DataFrame()

        # read data
        if self.datastart>0:
            self._data = self._readgws()
        else:
            self._data = DataFrame()

        return self._header, self._data


    def _findlines(self):
        """ Find start of header and data; if file has data at all """

        # set variables to find at zero
        self.headerstart = 0
        self.headerend = 0
        self.datastart = 0

        # find variables
        for il in range(len(self.flines)):

            if self.flines[il].startswith(self._missingdata):
                # put zonder gegevens
                self.errors.append([self.filepath,"Bestand bevat geen data"])
                self.hasheader = False
                self.hasdata = False
                break

            if self.flines[il].startswith(self._metatag): #("Locatie,Filternummer,Externe"):
                if not self.flines[il+1].startswith("B"): # er zijn geen headerlines onder de headerkop
                    self.hasheader = False
                    self.errors.append([self.filepath,"Bestand zonder header"])                               
                else:
                    while True:
                        il+=1
                        if self.flines[il].startswith("B"):
                            if self.headerstart==0:
                                self.hasheader = True                        
                                self.headerstart = il
                                #self.headerlength = 1
                            #else:
                            #    self.headerlength+=1
                        else: #voorbij laatste regel header
                            self.headerend = il
                            break
                            
            if self.flines[il].startswith(self._datatag): #("Locatie,Filternummer,Peildatum"):
                # bepaal eerste regelnummer met data
                il+=1
                if self.flines[il].startswith("B"):
                    self.hasdata = True
                    self.datastart = il
                else:
                    self.hasdata = False
                    self.errors.append([self.filepath,"Bestand zonder grondwaterstanden"])
                break
        il+=1
        # end of def findlines
        return self.headerstart, self.headerend, self.datastart

    @staticmethod
    def parse_dino_date(datestring,addtime=False):
        if isinstance(datestring, str):
            if datestring!="":                
                # string to datetime.datetime object
                if addtime==True: date = datetime.strptime(
                    datestring+" 12:00", "%d-%m-%Y %H:%M")
                else: date = datetime.strptime(datestring, "%d-%m-%Y")                    
                
                ## replace invalid date with np.NaN
                ##if date.year < 1900: date = np.NaN
                ##elif date.year > datetime.now().year: date = np.NaN

            else:
                date = np.NaN
        else:
            date = np.NaN
        return date

    def _readheader(self): #public
        """ Read header data and return pandas dataframe """


        if self.headerstart>0 and self.headerend > self.headerstart:
            # create _header
            headerlist = [line[:-1].split(sep) for line in self.flines[self.headerstart:self.headerend]]
            self._header = DataFrame(headerlist, columns=self._header_cols)
            self._headertext = DataFrame(headerlist, columns=self._header_cols)

            # transform column values
            self._header["filter"] = self._header["filter"].apply(lambda x: x.lstrip("0"))
            self._header["mvdatum"] = self._header["mvdatum"].apply(lambda x:self.parse_dino_date(x))
            self._header["startdatum"] = self._header["startdatum"].apply(lambda x:self.parse_dino_date(x))
            self._header["einddatum"] = self._header["einddatum"].apply(lambda x:self.parse_dino_date(x))

            # make seriesname
            ##self.seriesname = self._header["nitgcode"].values[0]+"_"+str(self._header["filter"].values[0])
        else:
            # create empty dataframe
            self._header = DataFrame(columns=self._header_cols)
            self._headertext = DataFrame(columns=self._header_cols)
            self.seriesname = "onbekend" # self.filename.split(".")[0]
            #print("warning : series has no header")
        return self._header


    def _readgws(self):
        """ Read groundwater measurements to pandas data frame """

        def fstr2float(astr):
            try:
                aval = float(astr)
            except ValueError:
                aval = np.NaN
            return aval


        if self.datastart>0:

            # create list of data from filelines
            data = [line[:-1].split(sep)[0:7]+[sep.join(line[:-1].split(sep)[7:])] for line in self.flines[self.datastart:]]            
            self._datatext = DataFrame(data,columns=self._data_cols)
            self._data = DataFrame(data,columns=self._data_cols)

            # transform column values
            self._data["peildatum"] = self._data["peildatum"].apply(lambda x:datetime.strptime(x,"%d-%m-%Y"))  # 28-03-1958
            self._data["filter"] = self._data["filter"].apply(lambda x: x.lstrip("0"))
            self._data["standcmmp"] = self._data["standcmmp"].apply(lambda x: fstr2float(x))
            self._data["standcmmv"] = self._data["standcmmv"].apply(lambda x: fstr2float(x))
            self._data["standcmnap"] = self._data["standcmnap"].apply(lambda x: fstr2float(x))
            self._data["opmerking"] = self._data["opmerking"].apply(lambda x: x.strip(","))

        else:
            self._data = DataFrame(columns=self._data_cols)
            self._datatext = DataFrame(columns=self._data_cols)
        return self._data

    def series(self,units="cmmv"):
        """ Return groundwater measurements as pandas time series 
        Possible values for parameter units are : "cmmv", "cmmp" or "cmnap"
        """
        # create series from _data
        if len(self._data)>0:
            if units=="cmmv":
                # data = self.data[self.data["standcmmv"]!=""] # alle ontbrekende waarden eruit
                self.srseries = Series(self._data["standcmmv"].values, index=self._data["peildatum"],name=self.srname())
            if units=="cmmp":
                self.srseries = Series(self._data["standcmmp"].values, index=self._data["peildatum"],name=self.srname())
            if units=="cmnap":
                self.srseries = Series(self._data["standcmnap"].values, index=self._data["peildatum"],name=self.srname())
        else: # create empty series
            self.srseries = Series(name=self.srname())
        return self.srseries


    def headdata(self):
        """Return head data fromdino csv file"""

        if len(self._data)>0:
            data = self._data[self._head_cols].copy()
        else:
            data = DataFrame(columns=self._head_cols)

        return data


    def header(self):
        """ Return raw metadata from series as a pandas dataframe """        
        return self._header


    def data(self):
        """ Return raw data as Pandas dataframe """
        return self._data


    def locname(self,newname=None):
        if newname!=None: 
            self.location = newname
        elif not self.header().empty:
            self.location = self._header.loc[0,"nitgcode"]
            ##self.location = self._header.at[0,"nitgcode"]
        else:
            self.location = "B00A0000"
        return self.location


    def filname(self,newname=None):
        if newname!=None: 
            self.filter = newname
        elif not self.header().empty:
            self.filter = self.header().loc[0,"filter"]
        else: self.filter = "0"
        return self.filter


    def srname(self):
        self.seriesname = self.locname()+"_"+self.filname()
        return self.seriesname


    def describe(self):
        """ Return one line of metadata from series as a pandas dataframe """

        # deze functie moet eruit geschreven worden omdat parse_dino_date dit al afvangt
        def valdate(date):
            """ Validate datetime (no dates before 1900) """
            return (date.strftime("%d-%m-%Y") if date.year>1900 else np.NaN)

        if self.dfdesc.empty:
            filcols = ['reeksnaam', 'nitgcode', 'filter', 'tnocode', 'xcoor', 'ycoor','mvcmnap', 'mvdatum', 'startdatum', 'einddatum', 'mpcmnap', 'mpcmmv','filtopcmnap', 'filbotcmnap']
            self.dfdesc = DataFrame(columns=filcols)

            if len(self._readheader()) !=0 and len(self._readgws())!=0:

                # make one line of metadata
                dftail = self.header().tail(1).copy()

                # insert series name as first column
                ##dftail['reeksnaam'] = dftail["nitgcode"]+"_"+dftail["filter"].values.astype('str')
                dftail['reeksnaam'] = self.srname()

                # recalculate startdate and enddate from measurements
                colnr = dftail.columns.get_loc("startdatum")
                startdatestr = self.data()["peildatum"][0]
                dftail.iloc[0,colnr] = pd.to_datetime(valdate(startdatestr),format='%d-%m-%Y')
                
                colnr = dftail.columns.get_loc("einddatum")
                enddatestr   = self.data()["peildatum"][len(self.data())-1]
                dftail.iloc[0,colnr]  = pd.to_datetime(valdate(enddatestr),format='%d-%m-%Y')

                self.dfdesc = dftail.reindex(columns=filcols).copy()
                self.dfdesc = self.dfdesc.reindex() # set index to 0

        return self.dfdesc


    def mpref(self):
        """ create dataframe with series of mp reference changes (for plotting line of ref changes above gwseries graph)"""
        msg = 'mpref method is depricates. use GwSeries.tubepropchanges() instead.'
        warnings.warn(msg, warnings.DeprecationWarning)


    def locations(self,df=DataFrame()):
        """ create table of locations from dataframe with data from several filters created by function describe() """

        # select one row for each group of filters
        grp = df.groupby("nitgcode")
        dfloc = grp.last()
        dfloc["startdatum"] = grp["startdatum"].min()
        dfloc["einddatum"] = grp["einddatum"].max()
        dfloc["nfil"] = pd.to_numeric(grp["filter"].count())

        # add index as column and reindex rows
        dfloc.insert(0,"nitgcode",dfloc.index)
        dfloc = dfloc.reset_index(drop=True)

        # drop columns with filter specific data
        dropcols = ["reeksnaam","filter",'mpcmnap','mpcmmv','filtopcmnap','filbotcmnap']
        dfloc = dfloc.drop(dropcols,axis=1,inplace=False) #,axis=1)

        # reorder columns
        dfloc = dfloc.reindex(columns=['nitgcode','tnocode','nfil','mvcmnap','mvdatum','startdatum','einddatum','xcoor','ycoor'])

        return dfloc


    def merge(self,dn2):
        """ add series of dinogws object to dinogws object and return merged object """

        if not isinstance(self,dinogws):
            raise TypeError("Input of dinogws.merge() must be another dinogws object")

        
        if (not self._data.empty) and (not dn2._data.empty):

            # determine possible overlap
            startdate1 = self.data().peildatum.min()
            enddate1 = self.data().peildatum.max()
            startdate2 = dn2.data().peildatum.min()
            enddate2 =  dn2.data().peildatum.max()
            if (startdate2 <= enddate1) and (startdate1 <= enddate2):
                raise ValueError('date ranges from both series show overlap')

            # merge headers
            self._header = pd.concat([self._header,dn2._header])
            self._header = self._header.sort_values(by=['startdatum']).reset_index()

            # merge groundwater measurement data
            self._data = pd.concat([self._data,dn2._data]).sort_values(by=['peildatum'])

        return self


def filesfromdir(dir):
    """Return list of dino sourcefiles from directory """

    filenames = []
    seriesnames = []
    for root, dirs, files in os.walk(sourcedir):
        seriesnames += [f[0:11] for f in files if f[11:13]=="_1"]
        filenames += [os.path.join(root, f) for f in files if f[11:13]=="_1"]
    return filenames, seriesnames

