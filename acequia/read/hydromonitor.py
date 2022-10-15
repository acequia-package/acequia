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

from ..gwseries import GwSeries


class HydroMonitor:
    """Read and manage data from hydromonitor csv export file

    Methods
    -------
    get_series
        Return GwSeries object from HydroMonitor object.
    to_list
        Return time series data as list of GwSeries objects.
    to_json
        Save all data to json files.
    iterdata
        Return generator for iterating over heads data.
    idkeys
        Return column names that uniquely identify a series.
    delete_duplicate_data
        Remove duplicate data from data and return DataFrame.

    Examples
    --------
    Read hydromonitor csv export file:
    >>>hm = HydroMonitor.from_csv(filepath=<path>)
    Convert to list of GwSeries objects:
    >>>mylist = hm.to_list()
    Iterate over all series and return GwSeries objects one at a time:
    >>>for i in range(len(hm)):
        gw = next(hm)
    Iterate over raw data and returnGwSeries objects: 
    >>>for (loc,fil),data in hm.iterdata():
        gw = hm.get_series(data=data,loc=loc,fil=fil)
    Save all series to json files in <filedir>:
    >>>hm.to_json(<filedir>)
    """

    CSVSEP = ";"
    METATAG = 'StartDateTime'
    DATATAG = 'DateTime'

    META_NUMCOLS = ['XCoordinate','YCoordinate','SurfaceLevel',
        'WellTopLevel','FilterTopLevel','FilterBottomLevel',
        'WellBottomLevel',]

    MAPPING_TUBEPROPS = OrderedDict([
        ('startdate','StartDateTime'),
        ('mplevel','WellTopLevel'),
        ('filtop','FilterTopLevel'),
        ('filbot','FilterBottomLevel'),
        ('surfacedate',None),
        ('surfacelevel','SurfaceLevel'),
        ])

    def __init__(self,fpath):
        """
        Parameters
        ----------
        fpath : str
            Valid filepath to hydromonitor csv file.
        """
        self.fpath = fpath

        # read header and line numbers from csv
        self.header, self._line_numbers, self.meta_colnames, self.data_colnames = self._readcsv()

        # extract metadata and data from file
        self.metadata, self.data = self._extract_contents()

        # remopve duplicate data
        self.data = self.delete_duplicate_data()

        # create generator
        self._srgen = self.data.groupby(self.idkeys()).__iter__()
        self._itercount = 0


    def __repr__(self):
        return (f'{self.__class__.__name__}') # ({len(self.metadata)} filters)')


    def _readcsv(self):
        """ Read hydromonitor csv export file """

        try:
            textfile = open(self.fpath)
        except IOError:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.fpath)
            textfile = None
        else:
            header, line_numbers, metacols, datacols = self._read_header(textfile)
            textfile.close()

        return header, line_numbers, metacols, datacols


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
                metafirst = i+2
                #metacols = [x.lower() for x in linelist]
                metacols = [x for x in linelist]

            # read data line number column names
            elif self.DATATAG in line:
                datatag_found = True
                datafirst = i+2
                metalast = i-2
                datacols = [x.lower() for x in linelist]
                datacols = [x for x in linelist]
                break # avoid iterating over lines after metadata

        # warnings
        if not metatag_found:
            warnings.warn(f'Metadata header {self.METATAG} not found.')

        if not datatag_found:
            warnings.warn(f'Data header {self.DATATAG} not found.')

        # return variables
        header = Series(header)
        line_numbers = Series({'metafirst':metafirst,'metalast':metalast,
            'datafirst':datafirst},name='line_numbers')

        return header, line_numbers, metacols, datacols


    def _extract_contents(self):

        content_list = [x for x in self.header['file_contents']]
        if 'Metadata' in content_list:
            # this is where the work gets done
            metadata = self._read_metadata()
        else:
            metadata = None
            warnings.warn("Metadata not specified.")

        if 'Data' in content_list:
            if metadata is None:
                raise((f'Heads from {filepath} can not be read '
                      f'because metadata are not available.'))
            # this is where the work gets done
            data = self._read_data()
        else:
            data = None
            warnings.warn("Data not specified.")

        return metadata,data

    def _read_metadata(self):
        """ read metadata from hydromonitor csv export file """

        #Name;NITGCode;OLGACode;FilterNo;StartDateTime;XCoordinate;
        #YCoordinate;SurfaceLevel;WellTopLevel;FilterTopLevel;
        #FilterBottomLevel;WellBottomLevel;LoggerSerial;LoggerDepth;
        #Comment;CommentBy;Organization;Status;

        firstrow = self._line_numbers['metafirst'] 
        lastrow = self._line_numbers['metalast']
        nrows = (lastrow - firstrow + 1)

        # use pandas csv reader to read metadata
        meta = pd.read_csv(
            self.fpath,
            sep=self.CSVSEP,
            index_col=False,
            header=None,
            names=self.meta_colnames,
            skiprows=firstrow,
            nrows=nrows,
            dtype=str,
            encoding='latin-1',
            )

        # delete empty last column
        if '' in list(meta.columns):
            meta = meta.drop([''], axis=1)

        # convert datetime column
        meta['StartDateTime'] = pd.to_datetime(meta['StartDateTime'],
            format='%d-%m-%Y %H:%M',errors='coerce')

        for col in self.META_NUMCOLS:
            meta[col] = pd.to_numeric(meta[col],errors='coerce')

        return meta

    def _read_data(self):
        """ read data from hydromonitor csv export file """

        #read data
        data = pd.read_csv(
            self.fpath,
            sep=self.CSVSEP,
            index_col=False,
            header=None,
            names=self.data_colnames,
            skiprows=self._line_numbers['datafirst'],
            #parse_dates=['datetime'], # don't, this takes a lot of time
            dtype=str,
            encoding='latin-1',
            )

        if 'LoggerHead' not in self.data_colnames:
        # when no loggerhead is available, menyanthes only exports
        # the column manualheads and the column loggerheads is simply missing
        # this happens when loggerdata without manual control measurments
        # are imported from another source; Menyanthes marks these 
        # measurements as manual heads.

            pos = data.columns.get_loc('DateTime')+1
            data.insert(loc=pos,column='LoggerHead',value=np.nan)

            msg = f'Missing data column LoggerHead added and filled with NaNs'
            warnings.warn(msg)

        if 'ManualHead' not in self.data_colnames:
        # this is a variation on the previous missing loggerhead issue

            pos = len(data.columns)
            data.insert(loc=pos,column='ManualHead',value=np.nan)
            #dfdata['manualhead'] = np.nan

            msg = f'Missing data column LoggerHead added and filled with NaNs'
            warnings.warn(msg)


        # delete empty last column
        if '' in list(data.columns):
            data = data.drop([''], axis=1)

        # delete repeating headers deep down list of data as a result of
        # annoying bugs in menyanthes export module
        namecol = self.data_colnames[0]
        #data = data[data[namecol]!='NITGCode'].copy()
        #data = data[data[namecol]!='Name'].copy()
        data = data[data[namecol]!=namecol].copy()
        data = data[data[namecol]!='[String]'].copy()

        # parsing these dates is very time consuming
        data['DateTime'] = pd.to_datetime(data['DateTime'],
              dayfirst=True,format='%d-%m-%Y %H:%M',errors='coerce')
        data['LoggerHead'] = pd.to_numeric(data['LoggerHead'], 
                               errors='coerce')
        data['ManualHead'] = pd.to_numeric(data['ManualHead'], 
                               errors='coerce')
        return data

    def idkeys(self):
        """Return column names that give a unique identification of a 
        series """
        # bug in hydromonitor export? id is allways nitgcode, filterno
        # idkeys = ['nitgcode','filterno']
        if len(self.header['object_identification'])>2:
            message.warn('More than two object identification keys given')
        return [x for x in self.header['object_identification']]


    def delete_duplicate_data(self):
        """Remove duplicate data from data and return pd.DataFrame
        Duplicates occur in groundwater head measurments in
        hydromonitor export when loggervalue and manual control 
        measurement have the same timestamp."""
        sortcols = self.idkeys() + ['DateTime','ManualHead']
        data = self.data.sort_values(by=sortcols)
        dropcols = self.idkeys() + ['DateTime']
        self.data_no_dups = data.drop_duplicates(subset=dropcols, 
                            keep='first').copy()
        return self.data_no_dups


    def get_series(self,loc=None,fil=None):
        """Return GwSeries object from HydroMonitor object
        Parameters
        ----------
        loc : str
            Well location name
        fil : str
            Tube name
        Returns
        -------
        GwSeries object
        """

        gws = GwSeries()
        
        # create DataFrame with HydroMonitor metadata for one series
        bool_loc = self.metadata[self.idkeys()[0]]==loc
        bool_fil = self.metadata[self.idkeys()[1]]==fil
        metadata = self.metadata[bool_loc & bool_fil]
        if metadata.empty:
            raise ValueError((f"Combination of loc='{loc}' and fil='{fil}' "
                f"not found in HydroMonitor metadata."))

        # Metadata can have a new row of metadata for each change.
        # Therefore, metaqdata can one or mulitple rows. For GwSeries
        # locprops items
        # all rows have the same value and metadata are simply taken 
        # from the first row.
        idx_firstrow = metadata.index[0]

        # create DataFrame with Hydromonitor measurements for one series
        bool_loc = self.data[self.idkeys()[0]]==loc
        bool_fil = self.data[self.idkeys()[1]]==fil
        data = self.data[bool_loc & bool_fil]

        # GwSeries tubeprops from HydroMonitor metadata
        for prop in GwSeries._tubeprops_names: #list(gws._tubeprops):
            metakey = self.MAPPING_TUBEPROPS[prop]
            if metakey is not None:
                gws._tubeprops[prop] = metadata[metakey].values
            if prop not in self.MAPPING_TUBEPROPS.keys():
                warnings.warn(f"Unknown property {prop} in {type(gws)}")

        # GwSeries locprops from HydroMonitor metadata
        for prop in GwSeries._locprops_names: ##list(gws._locprops.index):

            if prop=='locname':
                gws._locprops[prop] = metadata.at[idx_firstrow,self.idkeys()[0]]
            
            if prop=='filname':
                gws._locprops[prop] = metadata.at[idx_firstrow,self.idkeys()[1]]

            if prop=='alias':
                if 'NITGCode' in self.idkeys(): 
                    alias_key = 'Name'
                else: 
                    alias_key = 'NITGCode'
                gws._locprops[prop] = metadata.at[idx_firstrow,alias_key]

            if prop=='xcr':
                gws._locprops[prop] = metadata.at[idx_firstrow,'XCoordinate']

            if prop=='ycr':
                gws._locprops[prop] = metadata.at[idx_firstrow,'YCoordinate']

            if prop=='height_datum':
                gws._locprops[prop] = 'mnap'

            if prop=='grid_reference':
                gws._locprops[prop] = 'rd'

            if prop not in GwSeries._locprops_names:
                warnings.warn(f"Unknown property {prop} in {type(gws)}")

        # set gwseries
        datetimes = data['DateTime'].values
        heads = np.where(
            np.isnan(data['LoggerHead'].values),
            data['ManualHead'].values,
            data['LoggerHead'].values
            )
        rec = {}
        for key in GwSeries._headprops_names:
            if key=='headdatetime':
                rec[key] = datetimes
            elif key=='headmp':
                rec[key] = heads
            else: # all other columns in GwSeries headprops
                rec[key] = np.full(len(heads),np.nan)
        gws._heads = DataFrame(rec)

        
        # remove rows with invalid datevalues and warn
        mask = pd.isna(gws._heads['headdatetime'])
        number_of_bad_dates = len(heads[mask])
        if number_of_bad_dates!=0:
            msg = f"Removed {number_of_bad_dates} rows with invalid date from {gws.name()}"
            warnings.warn(msg)
            heads = heads[~mask].copy()

        # convert heads in mnap to mref
        heads = gws._heads['headmp'].copy()
        dates = gws._heads['headdatetime'].copy()
        for idx, props in gws._tubeprops.iterrows():
            mask = dates >= props['startdate'] 
            heads = heads.mask(mask,props['mplevel']-heads)
        gws._heads['headmp'] = heads
        return gws

    def to_list(self):
        """ Return data from HydroMonitor as a list of GwSeries() 
            objects """

        srlist = []

        heads = self.delete_duplicate_data()
        filgrp = heads.groupby(self.idkeys())
        for (location,filnr),data in filgrp:

            gws = self.get_series(loc=location,fil=filnr)
            srlist.append(gws)

        return srlist


    def __iter__(self):
        return self


    def __next__(self):

        if self._itercount >= len(self):
            raise StopIteration

        (loc,fil),data = next(self._srgen)
        gw = self.get_series(loc=loc,fil=fil)

        self._itercount+=1
        return gw

    def iterdata(self):
        """Return generator for iterating over heads data"""
        heads = self.delete_duplicate_data()
        return heads.groupby(self.idkeys()).__iter__()

    def __len__(self):
        heads = self.delete_duplicate_data()
        hymlen=0
        for srname,sr in heads.groupby(self.idkeys()).__iter__():
            hymlen+=1
        return hymlen

    def to_json(self,filedir=None):

        for (loc,fil),data in self.iterdata():
            gws = self.get_series(loc=loc,fil=fil)
            gws.to_json(filedir)
