

"""

Object for maintaining a groundwater series iterator

T.J. de Meij januari 2020

""" 

import os
from pandas import Series, DataFrame
import pandas as pd
import time
from datetime import datetime

import acequia as aq

import logging
logger = logging.getLogger(__name__)


def headsfiles(srcdir=None,srctype=None,loclist=None):
    """Return list of sourcefiles

    Parameters
    ---------
    srcdir : str
        directory with sourcefiles

    srctype : {'dinocsv','json'}
        sourcefiletype

    loclist : list, optional
        list of strings with location names

    Return
    ------
    pd.DataFrame with series sourcefilelist

    """
    gws = aq.GwList(srcdir=srcdir,srctype=srctype,loclist=loclist)
    return gws.filelist()


class GwList():
    """
         for list of GwSeries objects
    """

    def __repr__(self):
        return (f'{self.__class__.__name__}()')


    def __init__(self,srcdir=None,srctype='dinocsv',loclist=None,
        srcfile=None):
        """Container for list of GwSeries objects  

        Variables
        ---------
        srcdir : str, optional
            directory with groundwater level sourcefiles
        srctype : {'dinocsv','json','hymon'}
            sourcefiletype
        loclist : list
            list of location names
        srcfile : str, optional
            path to sourcefile with list of sourcefiles (srctype 'json'
            or ' dinocsv' or file with heads data (srctype ' hymon')

        Examples
        --------        
        Loading sourcefiles:
        >>>gwl = GwList(srcdir=<sourcedir>,srctype='dinocsv',loclist=<mylist>)
        >>>gwl = GwList(srcdir=<sourcedir>,srctype='json',loclist=<mylist>)
        >>>gwl = GwList(srcfile=<filepath>,srctype=<'json' or ' dinocsv'>)
        >>>gwl = GwList(srfile=<hydromonitor csv export>,srctype='hymon')

        Printing string repr of al GwSeries objects:
        >>>for i,gw in enumerate(gwl):
               print(i,gw)

        Table with location properties:
        >>>locp = gwl.locprops()

        List of soourcefiles in <srcdir> of type ' dinocsv':
        >>>gwl.filelist()

        Notes
        -----
        When only srcdir and srctype are given, result will be a list of
        GwSeries objects for all sourcefiles in srcdir.

        When loclist is given, names in this list will be used for 
        selecting files in srcdir (if a filename contains any of the 
        names in loclist, the file will be selected).

        Sourcefiles can be given in two different ways: srcdir or 
        srcfile. When values for both srcdir and srcfile are given, 
        srcfile will be ignored.

        """
        self.srcdir = srcdir
        self.srctype = srctype
        self.loclist = loclist
        self.srcfile = srcfile


        if self.srctype not in ['dinocsv','json','hymon']:

            raise ValueError(' '.join(
                f'{self.srctype} is not a valid sourcefile type. Valid',
                f'(sourcefiletype must be given.',))


        if (self.srcdir is None) and (self.srcfile is None):

            raise ValueError(' '.join(
                f'At least one of parameters srcdir or srclist must',
                f'be given.',))


        if (self.srcdir is not None) and (self.srcfile is not None):

            self.srcfile = None # given value for srcfile is ignored!
            msg = ' '.join(
                f'Ambigious combination of parameter values: srcdir is',
                f'{self.srcdir} (not None) and srcfile is {self.srcfile}',
                f'(not None). Given value for srcfile will be ignored.',)
            logger.warning(msg)


        if self.srcdir is not None:

            if not os.path.isdir(self.srcdir):
                raise ValueError(f'Directory {srcdir} does not exist')

            if self.srctype not in ['dinocsv','json']:
                msg = ' '.join(
                    f'Invalid parameter value: When srcdir is given',
                    f'srctype must be \'dinocsv\' or \'json\', not',
                    f'{self.srctype}.',)
                raise ValueError(msg)

            self.flist = self.filelist()

        if (self.srcfile is not None) and (
            self.srctype in ['dinocsv','json']):

            if not os.path.exists(self.srcfile):
                raise ValueError(f'Filepath {self.srcfile} does not exist.')

            self.flist = self.filelist()

        if (self.srcfile is not None) and (self.srctype=='hymon'):

            self.hm = aq.HydroMonitor.from_csv(filepath=srcfile)
            ##self.hm_itr = self.hm.iterseries()
            ##self.gwlist = hm.to_list()

        self.itercount = 0


    def filelist(self):
        """ Return list of GwSeries objects from files in source 
        directory 

        Returns
        -------
        List of GwSeries objects

        """

        if (self.srcdir is not None) and (self.srctype 
                in ['dinocsv','json']):

            return self.sourcefiles()

        if (self.srcfile is not None) and (self.srctype in ['dinocsv','json']):

            ftime = datetime.fromtimestamp(os.path.getmtime(self.srcfile))
            fileage = datetime.now()-ftime
            if fileage.days > 1:
                logger.warning(
                f'Age of {self.srcfile} is {fileage.days} days.')

            #TODO: check if flist contains valid sourcefilenames

            ## flist must be a list of sourcefilesnames
            flist = pd.read_csv(self.srcfile,index_col=False)

            return flist

        if (self.srcfile is not None) and (self.srctype=='hymon'):
            msg = ' '.join([
                f'function filelist() not supported for sourcetype',
                f'\'hymon\' ',])
            logger.warning(msg)
            return None

        msg = ' '.join(
            f'Unexpected combination of given parameters. No list of',
            f'GwSeries objects is returned.',)
        logger.warning(msg)
        return None


    def __iter__(self):
        """ return iterator """
        return self


    def __next__(self):
        """ return next gwseries object in list """
        
        if self.itercount >= self.__len__():
            raise StopIteration

        if self.srctype == 'dinocsv':
            idx = self.flist.index[self.itercount]
            filename = self.flist.at[self.itercount,'path']
            self.gw = aq.GwSeries.from_dinogws(filename)
        elif self.srctype == 'json':
            idx = self.flist.index[self.itercount]
            filename = self.flist.at[idx,'path']
            self.gw = aq.GwSeries.from_json(filename)
        elif self.srctype == 'hymon':
            #self.gw = self.hm[self.itercount]
            self.gw = next(self.hm)

        self.itercount += 1
        return self.gw

    #def iterseries(self):
    #    heads = self.delete_duplicate_data()
    #    return heads.groupby(self.idkeys()).__iter__()

    ###Iterate over series and return GwSeries objects one at a time:
    ###>>>for (loc,fil),data in self.iterseries():
   
    def __len__(self):

        if self.srctype in ['dinocsv','json']:
            return len(self.flist)

        if self.srctype in ['hymon']:
            return len(self.hm)

    def sourcefiles(self):
        """ return list of sourcefiles in directory dir"""

        if self.srctype=='dinocsv':
            files = [f for f in os.listdir(self.srcdir) 
                     if os.path.isfile(os.path.join(self.srcdir,f)) 
                     and f.split('.')[1]=='csv'
                     and f[11:13]=="_1"]

            dnfiles = pd.DataFrame({"file":files})
            dnfiles["loc"] = dnfiles["file"].apply(lambda x:x[0:8])
            dnfiles["fil"] = dnfiles["file"].apply(
                                        lambda x:x[8:11].lstrip("0"))
            dnfiles["kaartblad"] = dnfiles["loc"].apply(lambda x:x[1:4])
            dnfiles["series"]= dnfiles["loc"]+"_"+dnfiles["fil"]
            dnfiles["path"]= dnfiles["file"].apply(lambda x:self.srcdir+x)

            if self.loclist is not None:
                mask = dnfiles['loc'].isin(self.loclist)
                dnfiles = dnfiles[mask].copy()

            return dnfiles

        if self.srctype=='json':
            files = [f for f in os.listdir(self.srcdir) 
                     if os.path.isfile(os.path.join(self.srcdir,f)) 
                     and f.split('.')[1]=='json']

            jsf = pd.DataFrame({"file":files})
            jsf["series"]= jsf["file"].apply(lambda x:x.split('.')[0])
            jsf["loc"] = jsf["series"].apply(lambda x:x.split('_')[0])
            jsf["fil"] = jsf["series"].apply(
                         lambda x:x.split('_')[-1].lstrip("0"))

            jsf["path"]= jsf['file'].apply(lambda x:os.path.join(
                                                    self.srcdir,x))

            if self.loclist is not None:
                mask = jsf['loc'].isin(self.loclist)
                jsf = jsf[mask].copy()

            return jsf


    def gwseries(self,srname):
        """ Return named GwSeries object from list"""

        if self.srctype in ['dinocsv','json']:
            row = self.flist[self.flist['series']==srname]
            indexval = row.index.values[0]
            filepath = self.flist.loc[indexval,'path']

        if self.srctype=='json':
            gw = aq.GwSeries.from_json(filepath)

        if self.srctype=='dinocsv':
            gw = aq.GwSeries.from_dinogws(filepath)

        if self.srctype=='hymon':
            for gw in self.hm:
                if gw.name==srname:
                    break

        return gw



    def locprops(self):
        """ Return dataframe of locprops for locations """

        for i,gw in enumerate(self):

            if i==0:
                srlist = [gw.locprops()]
            else:
                srlist.append(gw.locprops())

        series = pd.concat(srlist,axis=0)
        series.index.name = 'series'
        series.to_csv('pmg_series.csv')

        locs = series.groupby(by='locname').last()
        locs['nfil']=series.groupby(by='locname').size().values
        colnames = ['alias','nfil','xcr','ycr']
        locs = locs[colnames].copy()

        self.itercount = 0

        return locs
