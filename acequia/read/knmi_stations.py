""" This module contains the KnmiLocations class that returns a list of
all available KNMI stations on the KNMI website and creates tables with
KNMI stations numbers and names

Example
-------
>>> aq.knmilocations()

"""

import os,os.path
import requests
import pkgutil
from io import StringIO
import warnings
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import pandas as pd

import acequia as aq
from acequia import CrdCon


def knmilocations(stntype='prc'):
    """ Return table of KNMI stations as pd.DataFrame 
    
    Parameters
    ----------
    stntype : 'prc','wtr','all'
        type of knmi station

    Returns
    -------
    pd.DataFrame

    """

    knmi = aq.KnmiStations()

    if stntype not in ['prc','wtr','all']:
        msg = f'Variable stntype must be "prc","wtr" or "all" '
        raise ValueError(smg)
    
    if stntype=='prc':
        tbl = knmi.prc_stns()

    if stntype=='wtr':
        tbl = knmi.wtr_stns()

    if stntype=='all':
        tbl1 = knmi.prc_stns()
        tbl2 = knmi.wtr_stns()
        tbl = pd.concat([tbl1,tbl2])

    xnull = pd.isnull(tbl.xcr)
    ynull = pd.isnull(tbl.ycr)
    crnan = list(tbl[(xnull|ynull)].stn_name.values)
    if len(crnan)!=0:
        msg = [f'{len(crnan)} stations with missing coordinates removed ',
               f'from tabel: {crnan}']
        warnings.warn(''.join(msg))

    return tbl[(~xnull & ~ynull)]


class KnmiStations:
    """Retrieve KNMI list of all available station numbers and names
    from KNMI website 

    Methods
    -------
    prc_stns(filepath=None)
        return list of manual rain gauche locations

    wtr_stns(filepath=None)
        return list of weather station locations

    Note
    ----
    Downloading lists of KNMI stations from the website takes time. 
    Recommended use is to download these data only once and save 
    results as csv for further use.

    """

    PRC_CRD_FILE = 'precipitation_crd.csv'
    STN_COLS = ['stn_name','stn_type','xcr','ycr','lon','lat','alt']
    STN_INDEX = 'stn_nr'


    def __init__(self):

        # read list of precipitation station coordinates from 
        # local csv file within package
        try:
            csvfile = pkgutil.get_data(__package__,self.PRC_CRD_FILE)
            data = StringIO(str(csvfile,'latin-1'))
            self._prc_crd = pd.read_csv(data, index_col='stn_nr')       
        except FileNotFoundError:
            self._prc_crd = DataFrame()
            msg = [f'Local file {self.PRC_CRD_FILE} not found. ',
                   f'Coordinates in list of precipitation stations ',
                   f'will all be NaN.']
            warnings.warn(''.join(msg))


    def prc_stns(self,filepath=None):
        """ Return table of all available precipitation stations on KNMI site
        
        Parameters
        ---------
        filepath : str, optional
            filepath for writing csv file with precipitation station list

        Returns
        -------
        pd.DataFrame

        Example
        -------
        knmi = KnmiStations()
        dfprc = knmi.prc_stns('prc_stations.csv')

        Note
        ----
        Coordinates of precipitation stations are not available on the
        KNMI website. This functions reads coordinates from a local csv 
        file.

        Explanation on KNMI website can be found on:
        https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script

        """

        par = {}
        str1 = r'http://projects.knmi.nl/klimatologie/monv' 
        str2 = r'/reeksen/getdata_rr.cgi'
        url = str1+str2
        self._flines = requests.get(url,params=par).text.splitlines()

        prc_dict={}
        startline=-1
        for i,line in enumerate(self._flines):

            if startline>-1: # and i>=startline:
                linelist = line.split(',')
                stn = int(linelist[0])
                stn_name = linelist[4].strip()
                if not stn in prc_dict.keys(): 
                    prc_dict[stn]={'stn_name':stn_name}

            if line.startswith('STN,YYYYMMDD,'):
                startline=i+1

        prcstn = pd.DataFrame.from_dict(prc_dict, orient='index')
        #prcstn.index = prcstn.index.astype(dtype='str')
        prcstn.index.name = self.STN_INDEX
        prcstn['stn_type'] = 'prc' 

        nancols = [x for x in self.STN_COLS if x not in list(prcstn)]
        for col in nancols:
            prcstn[col]=np.nan
        newcols = [x for x in list(prcstn) if x not in self.STN_COLS]
        cols = self.STN_COLS+newcols
        prcstn = prcstn[cols]

        # fill in missing coordinates
        if not self._prc_crd.empty:
            xcrdict = self._prc_crd['xcrd'].to_dict()
            ycrdict = self._prc_crd['ycrd'].to_dict()
            for index,row in prcstn.iterrows():
                if index in xcrdict.keys():
                    prcstn.at[index,'xcr']=xcrdict[index]
                if index in ycrdict.keys():
                    prcstn.at[index,'ycr']=ycrdict[index]

            crdcon = CrdCon()
            for stn,sr in prcstn.iterrows():
                crdict = crdcon.RDtoWGS84(sr['xcr'],sr['ycr'])
                prcstn.at[stn,'lon'] = round(crdict['Lon'],3)
                prcstn.at[stn,'lat'] = round(crdict['Lat'],3)

        nmiss_xcr = prcstn['xcr'].isnull().sum()
        nmiss_ycr = prcstn['ycr'].isnull().sum()
        nmiss = max([nmiss_xcr,nmiss_ycr])
        if nmiss!=0:
            msg = [f'List of precipitation stations has {nmiss} ',
                   f'missing coordinates in total of {len(prcstn)} ',
                   f'stations.']
            warnings.warn(''.join(msg))

        if filepath:
            prcstn.to_csv(filepath,index=True)

        return prcstn


    def wtr_stns(self,filepath=None):
        """ Return table of all available KNMI weather stations 

        Parameters
        ---------        
        filepath : str, optional
            filepath for outputfile with list of wheater stations

        Returns
        -------
        pd.DataFrame

        Example
        -------
        knmi = KnmiStations()
        dfprc = knmi.wtr_stns('wtr_stations.csv')

        Note
        ----
        Explanation on KNMI website can be found on:
        https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script

        """

        HEADERLINE = '# STN      LON(east)   LAT(north)     ALT(m)  NAME'
        DATALINE = '# YYYYMMDD'

        # daily data from meteorological stations
        str1 = r'http://projects.knmi.nl/klimatologie'
        str2 = r'/daggegevens/getdata_dag.cgi'
        url=str1+str2
        par = {'stns':'ALL'}
        flines = requests.get(url,params=par).text.splitlines()

        # find first and last line of table with data in text
        startline=-1    
        for i,line in enumerate(flines):

            if line.startswith(HEADERLINE):
                startline=i+1

            if startline!=-1 and line.startswith(DATALINE):
                endline = i-2
                break

        # table stn numbers and metadata
        wht_dict={}
        for i,line in enumerate(flines[startline:endline+1]):
        
            linelist = line.split()
            stn = linelist[1].rstrip(':')
            stn_name = ' '.join(linelist[5:])
            lon = linelist[2]
            lat = linelist[3]
            alt = linelist[4]

            if not stn in wht_dict.keys(): 
                wht_dict[stn]={
                    'lon':lon,
                    'lat':lat,
                    'alt':alt,
                    'stn_name':stn_name,
                    }

        wtrstn = pd.DataFrame.from_dict(wht_dict, orient='index')
        wtrstn.index.name = self.STN_INDEX
        wtrstn['stn_type'] = 'wtr'

        nancols = [x for x in self.STN_COLS if x not in list(wtrstn)]
        for col in nancols:
            wtrstn[col]=np.nan

        newcols = [x for x in list(wtrstn) if x not in self.STN_COLS]
        cols = self.STN_COLS+newcols
        wtrstn = wtrstn[cols]

        crdcon = CrdCon()
        for stn,sr in wtrstn.iterrows():
            crddict = crdcon.WGS84toRD(sr['lon'],sr['lat'])
            wtrstn.at[stn,'xcr'] = round(crddict['xRD'],0)
            wtrstn.at[stn,'ycr'] = round(crddict['yRD'],0)

        nmiss_xcr = wtrstn['xcr'].isnull().sum()
        nmiss_ycr = wtrstn['ycr'].isnull().sum()
        nmiss = max([nmiss_xcr,nmiss_ycr])
        if nmiss!=0:
            msg = [f'List of precipitation stations has {nmiss} ',
                   f'missing coordinates in total of {len(wtrstn)} ',
                   f'stations.',]
            warnings.warn(''.join(msg))

        if filepath:
            wtrstn.to_csv(filepath,index=True)

        return wtrstn

