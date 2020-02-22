""" This module contains the KnmiLocations class that 
return a list af all available KNMI stations on the KNMI website 
and creates tables of KNMI stations numbers and names

@author: Thomas de Meij

"""

import os,os.path
import requests
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import warnings
#import logging
#import acequia as aq
from acequia import CrdCon

#from importlib_resources import files
#from importlib_resources.trees import as_file

#try:
#    import importlib.resources as pkg_resources
#except ImportError:
#    # Try backported to PY<37 `importlib_resources`.
#    import importlib_resources as pkg_resources

##from . import templates  # relative-import the *package* containing the templates


class KnmiLocations:
    """Retrieve KNMI list of all available station numbers and names
    from KNMI website """

    # file with coordinates of precipitation stations
    PRC_CRD_FILE='precipitation_crd.csv'

    def prec_stns(self,filepath=None):
        """ Return table of all available KNMI precipitation stations 
        
        Parameters
        ---------
        filepath : str, optional
            filepath for writing csv file with precipitation station
            number and station name
            
        Returns
        -------
        pd.DataFrame

        Example
        -------
        knmi = KnmiLocations()
        dfprc = knmi.prec_sts('prc_stations.csv')

        Note
        ----
        Explanation on KNMI website can be found on:
        https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script

        """

        par = {}
        url = 'http://projects.knmi.nl/klimatologie/monv/reeksen/getdata_rr.cgi'
        flines = requests.get(url,params=par).text.splitlines()

        startline=0
        start = False
        prc_dict={}
        for i,line in enumerate(flines):

            if line.startswith('STN,YYYYMMDD,'):
                startline=i+1
                start=True
            
            if start and i>=startline:
                linelist = line.split(',')
                stn = int(linelist[0])
                stn_name = linelist[4].strip()
                if not stn in prc_dict.keys(): 
                    prc_dict[stn]={'stn_name':stn_name}

        prcstn = pd.DataFrame.from_dict(prc_dict, orient='index')
        prcstn.index.name = 'stn_nr'

        if filepath:
            prcstn.to_csv(filepath,index=True)

        return prcstn


    def weather_stns(self,filepath=None):
        """ Return table of all available KNMI weather stations 

        Parameters
        ---------        
        filepath : str, optional
            filepath for writing csv file with wheater station
            number, longitude, latitude and station name
            
        Returns
        -------
        pd.DataFrame

        Example
        -------
        knmi = KnmiLocations()
        dfprc = knmi.weather_sts('wht_stations.csv')

        Note
        ----
        Explanation on KNMI website can be found on:
        https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script

        """

        HEADERLINE = '# STN      LON(east)   LAT(north)     ALT(m)  NAME'
        DATALINE = '# YYYYMMDD'

        # daily data from meteorological stations
        url = 'http://projects.knmi.nl/klimatologie/daggegevens/getdata_dag.cgi'
        par = {'stns':'ALL'}
        flines = requests.get(url,params=par).text.splitlines()

        # find first and last line of table in text
        startline=0
        start = False        
        for i,line in enumerate(flines):

            if line.startswith(HEADERLINE):
                startline=i+1
                start=True
                
            if start==True and line.startswith(DATALINE):
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

        whtstn = pd.DataFrame.from_dict(wht_dict, orient='index')
        whtstn.index.name = 'stn_nr'

        # convert WGS84 to RD coordinates
        crdcon = CrdCon()
        for stn,sr in whtstn.iterrows():
            dict = crdcon.WGS84toRD(sr['lon'],sr['lat'])
            #print(dict['xRD'],dict['yRD'])
            whtstn.at[stn,'xcr'] = round(dict['xRD'],0)
            whtstn.at[stn,'ycr'] = round(dict['yRD'],0)

        if filepath:
            whtstn.to_csv(filepath,index=True)

        return whtstn


    def prec_coords(self,filepath=None,stntype='prec'):
        """ Return table with names and coordinates of knmi stations 

        Parameters
        ---------        
        filepath : str, optional
            path to file with station numbers
            (file made by prc_stns() or weather_stns()
        stntype : ['prec',wht']
            type of knmi station

        Results
        -------
        pd.DataFrame

        Note
        ----
        Coordinates of precipitation stations are not available on the
        KNMI website. This functions uses a table with coordinates from
        a local file.
        """

        # read local file with precipitation station coordinates
        try:
            dirname = os.path.join(os.path.dirname(__file__))
            csvfile = os.path.join(dirname,self.PRC_CRD_FILE)
            dfcrd = pd.read_csv(csvfile,index_col='stn_nr')
            dfcrd = dfcrd.drop(columns=['stn_name'])
        except OSError as e:
            message = ''.join([f'File {self.PRC_CRD_FILE} with precipitation',
                      f'station coordinates not found.'])
            raise #(message + str(e))

        # read or download table with available precipitation stations
        if filepath is None:
            prcstn = self.prec_stns()
        else:
            prcstn = pd.read_csv(filepath,index_col='stn_nr')

        # merge both files
        prcstn = pd.merge(prcstn,dfcrd,left_index=True,right_index=True,
                         how='left')

        # show stations with missing coordinates
        dfnan = prcstn[np.isnan(prcstn.xcrd) | np.isnan(prcstn.ycrd)]
        if len(dfnan)!=0:
            print()
            print(dfnan)
            print()
            message = f'Coordinates missing from {len(dfnan)} stations'
            #warnings.warn(message)

        return prcstn

