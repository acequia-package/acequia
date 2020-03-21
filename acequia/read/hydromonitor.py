"""This module contains the HydroMonitor object for reading groundwater
head measurements from a HydroMonitor csv export file

author:  Thomas de Meij
created: 02-03-2014
updated: 19-03-2020
"""

from collections import OrderedDict
import warnings
import matplotlib as mpl
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

##from acequia.gwseries import GwSeries
##import acequia.gwseries as GwSeries

#from acequia import GwSeries, DinoGws
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

    Example:
    -------
    hm = HydroMonitor.from_csv(filepath=<path>)
    mylist = hm.to_list()

    """

    CSVSEP = ";"
    METATAG = 'StartDateTime;XCoordinate;YCoordinate;'
    DATATAG = 'DateTime;LoggerHead;ManualHead;'


    mapping_tubeprops = OrderedDict([
        ('startdate','startdatetime'),
        ('mplevel','welltoplevel'),
        ('filtop','filtertoplevel'),
        ('filbot','filterbottomlevel'),
        ('surfdate',''),
        ('surflevel','surfacelevel'),
        ])



    def __repr__(self):
        ##return (f'{self.__class__.__name__} instance')
        return (f'{self.name()} (n={len(self._data)})')
        

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
        
        # read header and line_numbers
        textfile = self._open_file(self,filepath)
        self.header,self.line_numbers = self._read_header(self,textfile)
        textfile.close()

        content_list = [x.lower() for x in self.header['file_contents']]
        if 'metadata' in content_list:
            self.metadata = self._read_metadata(self)
        else:
            self.metadata = None
            warnings.warn("Metadata not specified.")

        if 'data' in content_list:
            self.data = self._read_data(self)
        else:
            self.data = None
            warnings.warn("Data not specified.")

        return self.header,self.metadata,self.data

    def _open_file(self,filepath):
        """ open hydromonitor csv file for reading and return file object """

        try:
            textfile = open(filepath,'r')

        except (IOError, TypeError) as err:
            errno, strerror = err.args
            print("{!s}".format(errno), end="")
            print("I/O fout{!s}".format(strerror), end="")
            print (" : "+filepath)
            textfile = None

        else:
            self.filepath = filepath

        return textfile

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
                self.metafirst = i+2
                self.metacols = [x.lower() for x in linelist]

            # read data line number column names
            elif self.DATATAG in line:
                self.datafirst = i+2
                self.metalast = i-2
                self.datacols = [x.lower() for x in linelist]
                break # avoid iterating over lines after metadata

        # return variables
        #self.header = DataFrame(header).T
        #self.header = DataFrame.from_dict(header,orient='index',columns=['value'])
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

        dfmeta['startdatetime'] = pd.to_datetime(dfmeta['startdatetime'],format='%d-%m-%Y %H:%M')
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

        # delete empty last column
        if '' in list(dfdata.columns):
            dfdata = dfdata.drop([''], axis=1)

        # delete repeating headers deep down list of data as a result of
        # annoying bugs in menyanthes export module
        dfdata = dfdata[dfdata.nitgcode!='NITGCode'].copy()
        dfdata = dfdata[dfdata.nitgcode!='[String]'].copy()

        # parsing these dates is very time consuming
        dfdata['datetime'] = pd.to_datetime(dfdata['datetime'],format='%d-%m-%Y %H:%M')
        dfdata['loggerhead'] = pd.to_numeric(dfdata['loggerhead'], errors='coerce')
        dfdata['manualhead'] = pd.to_numeric(dfdata['manualhead'], errors='coerce')

        return dfdata


    def to_list(self):
        """ Return data from HydroMonitor as a list of GwSeries() objects """

        srlist = []

        #srkeys = [x.lower() for x in self.header['object_identification']]
        # bug in hydromonitor export? id is allways nitgcode, filterno
        srkeys = ['nitgcode','filterno']
        if len(srkeys)>2:
            message.warn('More than two object identification keys given')

        # duplicates occur in hydromonitor export when loggervalue
        # and manual control measurement have the same timestamp
        sortcols = srkeys + ['datetime','manualhead']
        data = self.data.sort_values(by=sortcols)
        dropcols = srkeys + ['datetime']
        no_dups = data.drop_duplicates(subset=dropcols, keep='first').copy()
        self.no_dups = no_dups.copy()

        for (location,filter),sr in no_dups.groupby(srkeys):
            
            
            bool1 = self.metadata[srkeys[0]]==location
            bool2 = self.metadata[srkeys[1]]==filter
            metadata = self.metadata[bool1&bool2]
            firstindex = metadata.index[0]

            #gws = acequia.gwseries.GwSeries()
            gws = aq.GwSeries()

            for prop in list(gws._tubeprops):
                metakey = self.mapping_tubeprops[prop]
                if len(metakey)>0:
                    gws._tubeprops[prop] = metadata[metakey].values

                if prop not in self.mapping_tubeprops.keys():
                    warnings.warn(f"Unknown property {prop} in {type(gws)}")

            """
            # set tubeprops
            gws._tubeprops['startdate'] = metadata.startdatetime.values
            gws._tubeprops['mplevel'] = metadata.welltoplevel.values
            gws._tubeprops['filtop'] = metadata.filtertoplevel.values
            gws._tubeprops['filbot'] = metadata.filterbottomlevel.values
            gws._tubeprops['surflevel'] = metadata.surfacelevel.values
            """

            # set locprops
            for prop in list(gws._locprops.index):

                if prop=='locname':
                    gws._locprops[prop] = metadata.at[firstindex,srkeys[0]]
                
                if prop=='filname':
                    gws._locprops[prop] = metadata.at[firstindex,srkeys[1]]

                if prop=='alias':
                    if 'nitgcode' in srkeys: alias_key = 'name'
                    else: alias_key = 'nitgcode'
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
            heads = np.where(np.isnan(sr.loggerhead.values),sr.manualhead.values,sr.loggerhead.values)
            gws._heads = Series(data=heads,index=datetimes)

            srlist.append(gws)

        return srlist

