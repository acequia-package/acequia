"""This module contains the HydroMonitor object for reading groundwater
head measurements from a HydroMonitor csv export file

"""

from collections import OrderedDict
import warnings
import os.path
import errno
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


class HydroMonitor:
    """Read and manage data from hydromonitor csv export file
    
    Parameters:
    ---------
    header : pandas dataframe, optional
        header data from hydromonitor file as pandas dataframe
    metadata : pandas dataframe, optional
        metadata data from hydromonitor file as pandas dataframe
    data : pandas dataframe, optional
        measurements from hydromonitor file as pandas dataframe

    Examples:
    -------
    Read hydromonitor csv export file:
    >>>hm = HydroMonitor.from_csv(filepath=<path>)
    Convert to list of GwSeries objects:
    >>>mylist = hm.to_list()
    Iterate over series and return GwSeries objects one at a time:
    >>>for (loc,fil),data in self.iterseries():
           gw = self.get_series(sr=data,loc=loc,fil=fil)
    Save all series to json files in <filedir>:
    >>>hm.to_json(<filedir>)

    """

    CSVSEP = ";"
    METATAG = 'StartDateTime' #;XCoordinate;YCoordinate;'
    DATATAG = 'DateTime' #;LoggerHead;ManualHead;'


    mapping_tubeprops = OrderedDict([
        ('startdate','startdatetime'),
        ('mplevel','welltoplevel'),
        ('filtop','filtertoplevel'),
        ('filbot','filterbottomlevel'),
        ('surfacedate',''),
        ('surfacelevel','surfacelevel'),
        ])


    def __repr__(self):
        return (f'{self.__class__.__name__} instance')
      

    def __init__(self,header=None,metadata=None,data=None):
        """ Initialize HydroMonitor object """

        if isinstance(header, pd.Series):
            self.header = header
        else:
            if not header:
                self.header = DataFrame()
            else:
                message = 'header must be type None or type DataFrame'
                raise TypeError(message)

        if isinstance(metadata, pd.DataFrame):
            self.metadata = metadata
        else:
            if not metadata:
                self.metadata = DataFrame()
            else:
                message = 'meta must be type None or type DataFrame'
                raise TypeError(message)

        if isinstance(data, pd.DataFrame):
            self.data = data
        else:
            if not data:
                self.data = DataFrame()
            else:
                message = 'data must be type None or type DataFrame'
                raise TypeError(message)


    @classmethod
    def from_csv(cls,filepath):
        """ 
        read menyanthes hydromonitor csv export file

        parameters
        ----------
        filepath : str
            path to hydromonitor csv export file

        returns
        -------
        HydroMonitor object

        """
        header,metadata,data = cls._readcsv(cls,filepath)
        return cls(header=header,metadata=metadata,data=data)


    def _readcsv(self,filepath):
        """ Read hydromonitor csv export file """
        
        try:
            self.filepath = filepath
            textfile = open(self.filepath)
        except IOError:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), filepath)
            textfile = None
        else:
            self.header,self.line_numbers = self._read_header(self,textfile)
            textfile.close()

            content_list = [x.lower() for x in self.header['file_contents']]
            if 'metadata' in content_list:
                self.metadata = self._read_metadata(self)
            else:
                self.metadata = None
                warnings.warn("Metadata not specified.")

            if 'data' in content_list:
                if self.metadata is None:
                    raise(f'Heads from {filepath} can not be read ',
                          f'because metadata are not available.')                
                self.data = self._read_data(self)
            else:
                self.data = None
                warnings.warn("Data not specified.")
        #finally:

        return self.header,self.metadata,self.data


    def _read_header(self,textfile):
        """ 
        read header and linenumbers from hydromonitor export file 

        returns
        -------
        header : pandas dataframe
            header items as pandas dataframe
        filelines : tuple
            line numbers

        """

        metatag_found = False
        datatag_found = False

        header = OrderedDict()
        for i,line in enumerate(textfile):

            line = line.rstrip()
            linelist = line.split(self.CSVSEP)

            # read header tags
            if line.startswith('Format Name'):
                header['format_name']=linelist[1]
            elif line.startswith('Format Version'):
                header['format_version']=linelist[1]
            elif line.startswith('Format Definition'):
                header['format_definition']=linelist[1]
            elif line.startswith('File Type'):
                header['file_type']=linelist[1]
            elif line.startswith('File Contents'):
                values = list(filter(None, linelist[1:]))
                header['file_contents']=values
            elif line.startswith('Object Type'):
                header['object_type']=linelist[1]
            elif line.startswith('Object Identification'):
                values = list(filter(None, linelist[1:]))
                header['object_identification']=values

            # read metadata line number and column names
            elif self.METATAG in line:
                metatag_found = True
                self.metafirst = i+2
                self.metacols = [x.lower() for x in linelist]

            # read data line number column names
            elif self.DATATAG in line:
                datatag_found = True
                self.datafirst = i+2
                self.metalast = i-2
                self.datacols = [x.lower() for x in linelist]
                break # avoid iterating over lines after metadata

        # warnings
        if not metatag_found:
            msg = f'Metadata header {self.METATAG} not found.'
            warnings.warn(msg)

        if not datatag_found:
            msg = f'Data header {self.DATATAG} not found.'
            warnings.warn(msg)

        # return variables
        self.header = Series(header)
        self.line_numbers = (self.metafirst,self.metalast,self.datafirst)
        return self.header,self.line_numbers


    def _read_metadata(self):
        """ read metadata from hydromonitor csv export file """

        #Name;NITGCode;OLGACode;FilterNo;StartDateTime;XCoordinate;
        #YCoordinate;SurfaceLevel;WellTopLevel;FilterTopLevel;
        #FilterBottomLevel;WellBottomLevel;LoggerSerial;LoggerDepth;
        #Comment;CommentBy;Organization;Status;

        meta_nrows = self.metalast - self.metafirst + 1
        dfmeta = pd.read_csv(
            self.filepath,
            sep=self.CSVSEP,
            index_col=False,
            header=None,
            names=self.metacols,
            skiprows=self.metafirst,
            nrows=meta_nrows,
            dtype=str,
            encoding='latin-1',
            )

        # delete empty last column
        if '' in list(dfmeta.columns):
            dfmeta = dfmeta.drop([''], axis=1)

        dfmeta['startdatetime'] = pd.to_datetime(dfmeta['startdatetime'],
                                  format='%d-%m-%Y %H:%M',
                                  errors='coerce')

        numcols = ['xcoordinate','ycoordinate','surfacelevel',
                   'welltoplevel','filtertoplevel','filterbottomlevel',
                   'wellbottomlevel',]
        for col in numcols:
            dfmeta[col] = pd.to_numeric(dfmeta[col],errors='coerce')

        return dfmeta

    def _read_data(self):
        """ read data from hydromonitor csv export file """

        #read data
        dfdata = pd.read_csv(
            self.filepath,
            sep=self.CSVSEP,
            index_col=False,
            header=None,
            names=self.datacols,
            skiprows=self.datafirst,
            #parse_dates=['datetime'], # don't, this takes a lot of time
            dtype=str,
            encoding='latin-1',
            )

        if 'loggerhead' not in self.datacols:
        # when no loggerhead is available, menyanthes only exports
        # the column manualheads and the column loggerheads is simply missing
        # this happens when loggerdata without manual control measurments
        # are imported from another source; Menyanthes marks these 
        # measurements as manual heads.

            pos = dfdata.columns.get_loc('datetime')+1
            dfdata.insert(loc=pos,column='loggerhead',value=np.nan)

            msg = f'Missing data column loggerhead added and filled with NaNs'
            warnings.warn(msg)

        if 'manualhead' not in self.datacols:
        # this is a variation on the previous missing loggerhead issue

            pos = len(dfdata.columns)
            dfdata.insert(loc=pos,column='manualhead',value=np.nan)
            #dfdata['manualhead'] = np.nan

            msg = f'Missing data column loggerhead added and filled with NaNs'
            warnings.warn(msg)


        # delete empty last column
        if '' in list(dfdata.columns):
            dfdata = dfdata.drop([''], axis=1)

        # delete repeating headers deep down list of data as a result of
        # annoying bugs in menyanthes export module
        dfdata = dfdata[dfdata.nitgcode!='NITGCode'].copy()
        dfdata = dfdata[dfdata.nitgcode!='[String]'].copy()

        # parsing these dates is very time consuming
        dfdata['datetime'] = pd.to_datetime(dfdata['datetime'],
              dayfirst=True,format='%d-%m-%Y %H:%M',errors='coerce')
        dfdata['loggerhead'] = pd.to_numeric(dfdata['loggerhead'], 
                               errors='coerce')
        dfdata['manualhead'] = pd.to_numeric(dfdata['manualhead'], 
                               errors='coerce')
        return dfdata


    def idkeys(self):
        """Return column names that give a unique identification of a 
        series """
        # bug in hydromonitor export? id is allways nitgcode, filterno
        # idkeys = ['nitgcode','filterno']
        if len(self.header['object_identification'])>2:
            message.warn('More than two object identification keys given')
        return [x.lower() for x in self.header['object_identification']]


    def delete_duplicate_data(self):
        """Remove duplicate data from data and return pd.DataFrame

        Duplicates occur in groundwater head measurments in
        hydromonitor export when loggervalue and manual control 
        measurement have the same timestamp."""
        sortcols = self.idkeys() + ['datetime','manualhead']
        data = self.data.sort_values(by=sortcols)
        dropcols = self.idkeys() + ['datetime']
        self.data_no_dups = data.drop_duplicates(subset=dropcols, 
                            keep='first').copy()
        return self.data_no_dups


    def get_series(self,sr=None,loc=None,fil=None):
        """Return GwSeries object from HydroMonitor object

        Parameters
        ----------
        sr : pd.Series
            Timeseries with groundwater head values
        loc : str
            Well location name
        fil : str
            Tube name

        Returns
        -------
        GwSeries object

        """

        gws = aq.GwSeries()

        # select metadata for series 
        bool1 = self.metadata[self.idkeys()[0]]==loc
        bool2 = self.metadata[self.idkeys()[1]]==fil
        metadata = self.metadata[bool1&bool2]
        firstindex = metadata.index[0]

        # set tubeprops from hydro,onitor metadata
        for prop in list(gws._tubeprops):
            metakey = self.mapping_tubeprops[prop]
            if len(metakey)>0:
                gws._tubeprops[prop] = metadata[metakey].values
            if prop not in self.mapping_tubeprops.keys():
                warnings.warn(f"Unknown property {prop} in {type(gws)}")

        # set locprops from hydro,onitor metadata
        for prop in list(gws._locprops.index):

            if prop=='locname':
                gws._locprops[prop] = metadata.at[firstindex,self.idkeys()[0]]
            
            if prop=='filname':
                gws._locprops[prop] = metadata.at[firstindex,self.idkeys()[1]]

            if prop=='alias':
                if 'nitgcode' in self.idkeys(): 
                    alias_key = 'name'
                else: 
                    alias_key = 'nitgcode'
                gws._locprops[prop] = metadata.at[firstindex,alias_key]

            if prop=='xcr':
                gws._locprops[prop] = metadata.at[firstindex,'xcoordinate']

            if prop=='ycr':
                gws._locprops[prop] = metadata.at[firstindex,'ycoordinate']

            if prop=='height_datum':
                gws._locprops[prop] = 'mnap'

            if prop=='grid_reference':
                gws._locprops[prop] = 'rd'

            if prop not in ['locname','filname','alias','xcr','ycr',
                            'height_datum','grid_reference']:

                warnings.warn(f"Unknown property {prop} in {type(gws)}")


        # set gwseries
        datetimes = sr.datetime.values
        heads = np.where(
                    np.isnan(sr.loggerhead.values),
                    sr.manualhead.values,
                    sr.loggerhead.values)
        heads = Series(data=heads,index=datetimes)

        # remove rows with invalid datevalues and warn
        NaTdate = pd.isna(heads.index)
        nNaT = len(heads[NaTdate])
        if nNaT!=0:
            msg = f"Removed {nNaT} rows with invalid date from {gws.name()}"
            warnings.warn(msg)
            heads = heads[~NaTdate].copy()

        # convert heads in mnap to mref
        gws._heads = heads
        for index,props in gws._tubeprops.iterrows():
            mask = gws._heads.index >= props['startdate'] 
            gws._heads = gws._heads.mask(
                         mask,props['mplevel']-heads)

        return gws

    def to_list(self):
        """ Return data from HydroMonitor as a list of GwSeries() 
            objects """

        srlist = []

        heads = self.delete_duplicate_data()
        filgrp = heads.groupby(self.idkeys())
        for (location,filnr),sr in filgrp:

            gws = self.get_series(sr=sr,loc=location,fil=filnr)
            srlist.append(gws)

        return srlist


    def iterseries(self):
        heads = self.delete_duplicate_data()
        return heads.groupby(self.idkeys()).__iter__()


    def to_json(self,filedir=None):

        for (loc,fil),data in self.iterseries():
            gws = self.get_series(sr=data,loc=loc,fil=fil)
            gws.to_json(filedir)
