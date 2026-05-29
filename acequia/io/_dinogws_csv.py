"""Module with DinoGwsCsv class for reading dinocsv files with measured groundwater heads. """


import os as _os
from datetime import datetime as _dt
import numpy as _np
import pandas as _pd

from .._core.gwseries import GwSeries

def get_gwseries_from_dinocsv(fpath):
    """Return contents from Dinoloket Groundwaterlevels csv file.
    
    Parameters
    ----------
    fath : string
        Valid path to dinoloket csv file with measured groundwater levels.
    
    Returns
    -------
    DinoGwsCsv
        Contents of dinoloket csv file.
            """
    return DinoGwsCsv(fpath)
    

class DinoGwsCsv:
    """Read TNO Dinoloket dinocsv file with groundwater measurement data."""

    SEP = ","

    METATAG = ','.join(
        ['Locatie','Filternummer','Externe aanduiding',
         'X-coordinaat','Y-coordinaat','Maaiveld (cm t.o.v. NAP)',
         'Datum maaiveld gemeten','Startdatum','Einddatum',
         'Meetpunt (cm t.o.v. NAP)','Meetpunt (cm t.o.v. MV)',
         'Bovenkant filter (cm t.o.v. NAP)',
         'Onderkant filter (cm t.o.v. NAP)'
        ])

    DATATAG = ','.join(
        ['Locatie','Filternummer','Peildatum',
         'Stand (cm t.o.v. MP)','Stand (cm t.o.v. MV)',
         'Stand (cm t.o.v. NAP)','Bijzonderheid','Opmerking','','',''
         ])

    MISSINGDATATAG = (f'Van deze put zijn geen standen opgenomen',
         f'in de DINO-database')

    DINOHEADERCOLS = ["nitgcode","filter","tnocode","xcoor",
        "ycoor","mvcmnap","mvdatum","startdatum","einddatum",
        "mpcmnap","mpcmmv","filtopcmnap","filbotcmnap"]

    DINODATACOLS = ["nitgcode","filter","peildatum","standcmmp",
        "standcmmv","standcmnap","bijzonderheid","opmerking"]

    DINODATACOLS_MINIMAL = ['peildatum', 'standcmmp', 'bijzonderheid', 
        'opmerking']

    DINOHEADERCOLS_NUMERIC = ['mvcmnap', 'mpcmnap', 'mpcmmv', 
        'filtopcmnap', 'filbotcmnap']

    DINODATACOLS_NUMERIC = ['standcmmp', 'standcmmv',
        'standcmnap']

    MAPPING_GWSERIES_DINOLOCPROPS = {
        'locname':'nitgcode',
        'filname':'filter',
        'alias':'tnocode',
        'alias2':_np.nan,
        'owner':_np.nan,
        'observer':_np.nan,
        'constructiondate':_np.nan,
        'surfacestable':_np.nan,
        'xcr':'xcoor',
        'ycr':'ycoor',
        'height_datum':'NAP',
        'grid_reference':'RD',
        }

    MAPPING_GWSERIES_DINOTUBEPROPS = {
        'startdate':'startdatum',
        'mplevel':'mpcmnap',
        'filtop':'filtopcmnap',
        'filbot':'filbotcmnap',
        'surfacedate':'mvdatum',
        'surfacelevel':'mvcmnap',
        }

    MAPPING_GWSERIES_DINOHEADPROPS = {
        'headdatetime':'peildatum',
        'headmp':'standcmmp',
        'headnote':'bijzonderheid',
        'remarks':'opmerking',
        }


    def __init__(self, filepath):
        """
        filepath : str
            Valid filepath to dinoloket csv file.
            
        """
        if filepath is None:
            raise InputError(f'Filepath to valid dinocsv file must be specified.')
        self._filepath = filepath

        # read file contents and return list of file lines.
        self._flines, self._errors = self._readfile(self._filepath)
        self._headerstart, self._headerend, self._datastart, self._errors = self._parselines(self._flines, self._errors)
        self._header = self._readheader(self._flines, self._headerstart, self._headerend)
        self._data = self._read_data(self._flines, self._datastart)

        if self._header.empty and not self._data.empty:
            # header line were missing, but measurement data are available.
            # try to cnstruct header from data, as much as possible
            #self._header = _pd.DataFrame(data=[[_np.nan]*len(self.DINOHEADERCOLS)], columns=self.DINOHEADERCOLS)
            #self._header = self._header.astype({'nitgcode':str, 'filter':str})
            self._header = _pd.DataFrame(columns=self.DINOHEADERCOLS)
            self._header.at[0,'nitgcode'] = self._data.at[0, 'nitgcode']
            self._header.at[0,'filter'] = self._data.at[0, 'filter']
            self._header.at[0,'startdatum'] = self._data.at[0, 'peildatum']


    def __repr__(self):
        return (f'{self.nitgcode()} (n={len(self)})')

    def __len__(self):
        return len(self._data)

    def _readfile(self, filepath):
        """Read DINO csv file and return list of filelines.
        
        Parameters
        ----------
        filepath : str
            Valid filepath to Dino csv file.

        Returns
        -------
        filelines
            List of file lines as string.
                            
        """
        try:
            file = open(filepath,'r')
        except (IOError, TypeError) as err:
            errno, strerror = err.args
            print("{!s}".format(errno), end="")
            print("I/O fout{!s}".format(strerror), end="")
            print (" : "+filepath)
            errors = ["File can not be opened"]
            flines=[]
            raise
        else:
            flines = file.readlines()
            file.close()
            errors = []
        return flines, errors


    def _parselines(self, flines, errors):
        """Parse list of file lines from dinofile to data."""

        headerstart=0
        headerend=0
        datastart=0

        # before parsing, assert file is valid ascii
        if len(flines)==0:
            errors.append(["Dinocsv is empty."])
            return headerstart, headerend, datastart, errors
        elif flines[0][0]=='\x00':
            # test for corrupted file with only 'x00' 
            # Yes, I have really seen this kind of files!
            errors.append(["Dinocsv is corrupted."])
            return headerstart, headerend, datastart, errors

        # find variables
        for i in range(len(flines)):

            if flines[i].startswith(self.MISSINGDATATAG):
                # no measurmeents available
                errors.append(["Dinocsv file contains no data."])
                hasheader = False
                hasdata = False
                break

            if flines[i].startswith(self.METATAG):
                if not flines[i+1].startswith("B"): # er zijn geen headerlines onder de headerkop
                    hasheader = False
                    errors.append(["Dinocsv file contains no header."])          
                else:
                    while True:
                        i+=1
                        if flines[i].startswith("B"):
                            if headerstart==0:
                                hasheader = True                        
                                headerstart = i
                        else: #voorbij laatste regel header
                            headerend = i
                            break
                            
            if flines[i].startswith(self.DATATAG):
                # bepaal eerste regelnummer met data
                i+=1
                if flines[i].startswith("B"):
                    hasdata = True
                    datastart = i
                else:
                    hasdata = False
                    errors.append(["Dinocsv file has no header."])
                break
        i+=1
        # end of def findlines
        return headerstart, headerend, datastart, errors


    def _readheader(self, flines, headerstart, headerend): 
        """Read header data and return pandas dataframe."""

        if headerstart==0 and headerend==0: 
            return _pd.DataFrame(columns=self.DINOHEADERCOLS)

        if headerstart==0 and headerend <= headerstart:
            return _pd.DataFrame(columns=self.DINOHEADERCOLS)

        headerlist = [line[:-1].split(self.SEP) for line in flines[headerstart:headerend]]
        header = _pd.DataFrame(headerlist, columns=self.DINOHEADERCOLS)

        return header


    def _read_data(self, flines, datastart):
        """Read groundwater measurements to pandas data frame."""

        def fstr2float(astr):
            try:
                aval = float(astr)
            except ValueError:
                aval = _np.nan
            return aval

        if datastart==0:
            data = _pd.DataFrame(columns=self.DINODATACOLS)
            return data

        # create list of data from filelines
        data = [line[:-1].split(self.SEP)[0:7]+[self.SEP.join(line[:-1].split(
            self.SEP)[7:])] for line in flines[datastart:]]
        data = _pd.DataFrame(data, columns=self.DINODATACOLS)


        return data


    def nitgcode(self):
        filename = _os.path.basename(self._filepath)
        filename, ext = _os.path.splitext(filename)
        loc = filename[:8]
        tube = int(filename[8:11])
        return f'{loc}_{tube}'


    def data(self):
        """Return measurements."""
        data = self._data.copy()
        data['filter'] = data['filter'].str.lstrip('0').astype('int')
        data['peildatum'] = _pd.to_datetime(data['peildatum']+" 12:00", dayfirst=True)

        for column in self.DINODATACOLS_NUMERIC:
            data[column] = data[column].replace(r'^\s*$', None, regex=True).astype('float64').fillna(_np.nan)

        # remove commas from fields
        data['bijzonderheid'] =  data['bijzonderheid'].str.replace(r"^.*$","",regex=True)
        data['opmerking'] = data['opmerking'].str.replace(r"^.*$","",regex=True)
        return data


    def header(self):
        """Return header data."""
        header = self._header.copy()
        
        header['filter'] = header['filter'].str.lstrip('0')
        with _pd.option_context("future.no_silent_downcasting", True):
            header['tnocode'] = header['tnocode'].replace(r'^\s*$', None, regex=True).infer_objects(copy=False)
        header['xcoor'] = header['xcoor'].astype('float64')
        header['ycoor'] = header['ycoor'].astype('float64')

        # convert date columns from string to datetime
        header["mvdatum"] = _pd.to_datetime(header["mvdatum"], dayfirst=True)
        header["startdatum"] = _pd.to_datetime(header["startdatum"], dayfirst=True)
        header["einddatum"] = _pd.to_datetime(header["einddatum"], dayfirst=True)

        for column in self.DINOHEADERCOLS_NUMERIC:
            with _pd.option_context("future.no_silent_downcasting", True):
                header[column] = header[column].replace(r'^\s*$', None, regex=True).fillna(_np.nan).astype('float64').infer_objects(copy=False)

        return header ##.convert_dtypes()


    def gwseries(self):
        """Return GwSeries object with dinocsv data."""

        if self._data.empty | self._header.empty:
            # return empty gwseries instance
            locprops = _pd.Series(index=GwSeries.LOCPROPS_NAMES, dtype='object')
            locprops['locname'] = self.nitgcode().split('_')[0]
            locprops['filname'] = self.nitgcode().split('_')[1]
            return GwSeries(locprops=locprops)

        # get location metadata
        locprops = _pd.Series(index=GwSeries.LOCPROPS_NAMES, dtype='object')
        for propname in GwSeries.LOCPROPS_NAMES:
            dinoprop = self.MAPPING_GWSERIES_DINOLOCPROPS[propname]
            if _pd.isnull(dinoprop):
                continue
            if dinoprop in self.DINOHEADERCOLS:
                locprops[propname] = self.header().at[0, dinoprop]

        locprops['grid_reference'] = 'RD'
        locprops['height_datum'] = 'mNAP'

        # get tube metadata
        tubeprops = _pd.DataFrame(columns=GwSeries.TUBEPROPS_NAMES)
        for prop in GwSeries.TUBEPROPS_NAMES:
            dinoprop = self.MAPPING_GWSERIES_DINOTUBEPROPS[prop]
            if dinoprop in self.DINOHEADERCOLS:
                # copy column with tube properties
                tubeprops[prop] = self.header().loc[:, dinoprop]
            if dinoprop in self.DINOHEADERCOLS_NUMERIC:
                # convert from cm to m
                tubeprops[prop] = tubeprops[prop]/100.

        # get head measurements
        heads = _pd.DataFrame(columns=GwSeries.HEADPROPS_NAMES)
        for prop in GwSeries.HEADPROPS_NAMES:
            dinoprop = self.MAPPING_GWSERIES_DINOHEADPROPS[prop]
            if dinoprop in self.DINODATACOLS_MINIMAL:
                heads[prop] = self.data()[dinoprop]
        heads['headmp'] = heads['headmp']/100.

        return GwSeries(heads=heads, locprops=locprops, tubeprops=tubeprops)

