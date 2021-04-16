
import pathlib
import collections
import datetime as dt
import numpy as np
from pandas import Series,DataFrame
import pandas as pd


class DinoSurfaceLevel:
    """Read TNO Dinoloket csv file with surface water level measurements """

    SEP = ','
    QUOTE = '"'
    SINGLEQUOTE = '\''
    SPACE = ' '

    HEADERNAMES = ['nitgcode','alias','xcr','ycr','startdate','enddate',
        'dummy']

    HEADERTYPES = {'nitgcode':str,'alias':str,'xcr':np.float64, 
        'ycr':np.float64,'startdate':str,'enddate':str,'dummy':str}

    DATANAMES = ['nitgcode','date','level','remark','dummy']

    DATATYPES = {'nitgcode':str,'date':str,'level':np.float64,
        'remark':str,'dummy':str}


    def __repr__(self):
        ##return (f'{self.__class__.__name__} (n={len(self._data)})')
        return (f'{self.name()} (n={len(self._data)})')


    def __init__(self,fpath=None):

        self._fpath = fpath

        if self._fpath is None:
            raise TypeError(f'Parameter fpath must be given when '
                f'calling {self.__class__.__name__}()')

        ispath = isinstance(fpath,pathlib.Path)
        isstr = isinstance(self._fpath,str)
        if not ispath and not isstr:
            raise TypeError(f'Parameter fpath must be of type filepath'
                f'or type str, not type {type(fpath)}')

        if not pathlib.Path(self._fpath).exists():
            raise ValueError(f'Filepath {self._fpath} not found')


        self._flines = self._readfile()
        self._meta = self._parselines()
        self._header = self._read_header()
        self._data = self._read_data()


    def _readfile(self):
        """Return DINO csv filelines as list of strings"""

        # read csv file to list of strings
        try:
            self._file = open(self._fpath,'r')
        except:  
            self._flines = []
            raise
        else:
            self._flines = self._file.readlines()
            self._file.close()

        return self._flines


    def _parselines(self):
        """Return dino csv metadata as table and find linenumbers with
        start and end of header and data"""

        # parse header data and find linenumbers
        meta = collections.OrderedDict()

        for i,line in enumerate(self._flines):

            ##line = line.rstrip() #remove trailing newline
            elms = self._flines[i].rstrip().split(',')

            if line.startswith('Titel'):
                pass

            if line.startswith('Gebruikersnaam'):
                pass

            if line.startswith('Periode aangevraagd'):

                dtm = dt.datetime.strptime(elms[1],'%d-%m-%Y')
                meta['qrstart'] = dtm

                dtm = dt.datetime.strptime(elms[3],'%d-%m-%Y')
                meta['qrend'] = dtm

            if line.startswith('Gegevens beschikbaar'):

                dtm = dt.datetime.strptime(elms[1],'%d-%m-%Y')
                meta['datastart'] = dtm

                dtm = dt.datetime.strptime(elms[3],'%d-%m-%Y')
                meta['dataend'] = dtm

            if line.startswith('Datum'):

                dtm = dt.datetime.strptime(elms[1],'%d-%m-%Y')
                meta['request'] = dtm

            if line.startswith('Referentie'):

                meta['reference'] = elms[1]

            if line.startswith(f'Locatie,Externe aanduiding,X-coordinaat,'
                f'Y-coordinaat, Startdatum, Einddatum'):

                self._rowstart_header = i+1

            if line.startswith(f'Locatie,Peildatum,Stand (cm t.o.v. NAP)'
                f',Bijzonderheid'):

                self._rowstart_data = i+2 #there is an extra whiteline...

        # count number of header rows
        self._rowcount_header=0
        for i in range(self._rowstart_header,self._rowstart_data):
            if len(self._flines[i].rstrip())==0:
                break
            self._rowcount_header+=1
 
        return Series(meta)


    def _read_header(self):
        """Return header lines as table"""

        self._header = pd.read_csv(self._fpath, sep=self.SEP, header=0,
            names=self.HEADERNAMES, skiprows=self._rowstart_header-2,
            nrows=self._rowcount_header,dtype=self.HEADERTYPES,
            error_bad_lines=False)

        for colname in ['startdate','enddate']:
            self._header[colname] = pd.to_datetime(self._header[colname], 
                format='%d-%m-%Y', errors='coerce')

        return self._header


    def _read_data(self):
        """Return water level measurement data as table"""

        self._data = []
        for i,line in enumerate(self._flines):

            if i<self._rowstart_data:
                continue

            linedict = collections.OrderedDict()
            elms = self._flines[i].rstrip().split(self.SEP)

            # 'nitgcode','date','level', 'remarks','dummy'
            # process first 3 line elements
            for j in [0,1,2]:
                linedict[self.DATANAMES[j]] = elms[j]

            # proces remaining line elements as remarks
            stripchars = ''.join([self.SEP,self.SPACE,self.QUOTE,
                self.SINGLEQUOTE])
            remains = [x.strip(stripchars) for x in elms[3:]]
            remarks = self.SEP.join(remains).strip(stripchars)
            remarks = remarks.replace(self.SEP,'.')

            linedict[self.DATANAMES[3]] = remarks

            self._data.append(linedict)

        self._data = pd.DataFrame.from_dict(self._data)

        self._data['date'] = pd.to_datetime(self._data['date'], 
            format='%d-%m-%Y', errors='coerce')

        self._data['level'] = pd.to_numeric(self._data['level'],
            errors='coerce',downcast='integer')

        self._data['level'] = self._data['level']/100. #cm_to_m

        return self._data


    def locprops(self):
        """Return surface level gauge location properties"""
        colnames = ['nitgcode','alias','xcr','ycr']
        locp = self._header.loc[0,colnames]
        locp['reference'] = self._meta['reference']
        locp['grid_reference'] = 'RD'
        locp.name = 'locprops'
        return locp


    def levels(self):
        """Return surface water levels"""
        colnames = ['level'] #,'remark']
        levels = self._data.set_index('date')
        levels = levels[colnames]
        return levels


    def remarks(self):
        """Return table with dates and remarks"""
        mask = self._data['remark'].str.len()>0
        table = self._data[mask][['date','remark']]
        table = table.set_index('date',drop=True)
        return table


    def metadata(self):
        """Return metadata from header of dinocsv file"""
        return self._meta


    def name(self):
        """Return name of gauge"""
        return self._data.at[0,'nitgcode']

