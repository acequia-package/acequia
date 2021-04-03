"""

GwList is a class that holds a list of GwSeries objects and 
provides methodes for iterating
=======
GwList
======
Object for maintaining a groundwater series iterator


""" 

import os
import os.path
import warnings
from pandas import Series, DataFrame
import pandas as pd
import time
from datetime import datetime

import acequia as aq

##import logging
##logger = logging.getLogger(__name__)


def headsfiles(srcdir=None,srctype=None,loclist=None):
    """Return list of sourcefiles in directory

    Parameters
    ----------
    srcdir : str
        directory with sourcefiles

    srctype : {'dinocsv','json'}, optional
        sourcefiletype

    loclist : list, optional
        list of strings with location names

    Return
    ------
    pd.DataFrame with series sourcefilelist

    """
    gws = aq.GwList(srcdir=srcdir,srctype=srctype,loclist=loclist)
    return gws.filetable()


class GwList():
    """Holds a list of GwSeries objects

    Parameters
    ----------
    srcdir : str
        directory with groundwater head sourcefiles
    srctype : {'dinocsv','json','hymon'}, optional
        sourcefiletype
    loclist : list, optional
        list of location names
    srcfile : str, optional
        path to file with paths to sourcefiles
        (if srcfile is given, srcdir is ignored)

    Examples  
    --------  
    Create GwList object and load multiple sourcefiles:

    >>>gwl = GwList(srcdir=<sourcedir>,srctype='dinocsv',loclist=<mylist>)  

    >>>gwl = GwList(srcdir=<sourcedir>,srctype='json',loclist=<mylist>)    

    >>>gwl = GwList(srcfile=<filepath>,srctype=<'json' or ' dinocsv'>)    
    
    >>>gwl = GwList(srfile=<hydromonitor csv export>,srctype='hymon')  
  
    Return table with location properties:

    >>>locp = gwl.locprops()

    Return list of soourcefiles in <srcdir> of type ' dinocsv':

    >>>gwl.filelist()

    Notes
    -----
    When only srcdir is given, result will be a list of
    GwSeries objects for all sourcefiles in srcdir.

    When both srcdir and srcfile are given, all files from srcdir will
    be selected and srcfile will be ignored.

    When loclist is given, names in this list will be used for 
    selecting files in srcdir. All series that belong to a location
    will be selected as seperate series. For managing series that
    belong to one location, us the GwLocs object.
    
    
    """


    valid_srctype = ['dinocsv','json','hymon']

    def __repr__(self):
        mylen = len(self)
        return (f'{self.__class__.__name__}({mylen})')


    def __init__(self,srcdir=None,srctype='dinocsv',loclist=None,
        srcfile=None):
        """Return GwList object"""

        self.srcdir = srcdir
        self.srctype = srctype
        self.loclist = loclist
        self.srcfile = srcfile
        self._valid_srctype = ['dinocsv','json','hymon']


        """
        if self.srctype not in self._valid_srctype:

            msg = ' '.join([
                f'{self.srctype} is not a valid sourcefile type. Valid',
                f'sourcefiletypes are {self._valid_srctype}',
                ])
            raise ValueError(msg)
        """


        if (self.srcdir is None) and (self.srcfile is None):

            raise ValueError(' '.join(
                f'At least one of parameters srcdir or srclist must',
                f'be given.',))


        if (self.srcdir is not None) and (self.srcfile is not None):

            self.srcfile = None # given value for srcfile is ignored!
            msg = ' '.join([
                f'Ambigious combination of parameter values: srcdir is',
                f'{self.srcdir} (not None) and srcfile is {self.srcfile}',
                f'(not None). Given value for srcfile will be ignored.',])
            warnings.warn(msg)
            ##logger.warning(msg)


        if self.srcdir is not None:

            if not os.path.isdir(self.srcdir):
                raise ValueError(f'Directory {srcdir} does not exist')

            self._flist = self.filetable() #_sourcefiles()


        if (self.srcfile is not None) and (
            self.srctype in ['dinocsv','json']):

            if not os.path.exists(self.srcfile):
                raise ValueError(f'Filepath {self.srcfile} does not exist.')

            self._flist = self.filetable()

        if (self.srcfile is not None) and (self.srctype=='hymon'):

            self.hm = aq.HydroMonitor.from_csv(filepath=srcfile)

        self.itercount = 0


    def filetable(self):
        """ Return list of sourcefile names """

        # %timeit gwl.filelist()
        # 11.8 s ± 109 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

        if (self.srcdir is not None) and (self.srctype 
                in ['dinocsv','json']):

            return self._sourcefiles()

        if (self.srcfile is not None) and (self.srctype in ['dinocsv','json']):

            ftime = datetime.fromtimestamp(os.path.getmtime(self.srcfile))
            fileage = datetime.now()-ftime
            if fileage.days > 1:
                msg = f'Age of {self.srcfile} is {fileage.days} days.' 
                warnings.warn(msg)

            #TODO: check if flist contains valid sourcefilenames

            ## flist must be a list of sourcefilesnames
            flist = pd.read_csv(self.srcfile,index_col=False)

            return flist

        if (self.srcfile is not None) and (self.srctype=='hymon'):
            msg = ' '.join([
                f'function filelist() not supported for sourcetype',
                f'\'hymon\' ',])
            warnings.warn(msg)
            ##logger.warning(msg)
            return None

        msg = ' '.join([
            f'Unexpected combination of given parameters. No list of',
            f'GwSeries objects is returned.',])
        warnings.warn(msg)
        ##logger.warning(msg)
        return None


    def __iter__(self):
        """ return iterator """
        return self


    def __next__(self):
        """ return next gwseries object in list """
        
        if self.itercount >= self.__len__():
            raise StopIteration

        if self.srctype == 'dinocsv':
            idx = self._flist.index[self.itercount]
            filename = self._flist.at[self.itercount,'path']
            self.gw = aq.GwSeries.from_dinogws(filename)
 
        elif self.srctype == 'json':
            idx = self._flist.index[self.itercount]
            filename = self._flist.at[idx,'path']
            self.gw = aq.GwSeries.from_json(filename)

        elif self.srctype == 'hymon':
            #self.gw = self.hm[self.itercount]
            self.gw = next(self.hm)

        self.itercount += 1
        return self.gw

   
    def __len__(self):

        if self.srctype in ['dinocsv','json']:
            return len(self._flist)

        if self.srctype in ['hymon']:
            return len(self.hm)


    def _sourcefiles(self):
        """ return list of sourcefiles in directory dir"""

        if self.srctype=='dinocsv':

            pathlist = aq.listdir(self.srcdir, filetype='csv')
            filelist = [os.path.split(path)[-1] for path in pathlist if path.split('_')[-1].endswith('1.csv')]
            dnfiles = pd.DataFrame({"file":filelist})

            dnfiles["loc"] = dnfiles["file"].apply(lambda x:x[0:8])
            dnfiles["fil"] = dnfiles["file"].apply(
                lambda x:x[8:11].lstrip("0"))
            dnfiles["kaartblad"] = dnfiles["loc"].apply(lambda x:x[1:4])
            dnfiles["series"]= dnfiles["loc"]+"_"+dnfiles["fil"]
            dnfiles["path"]= dnfiles["file"].apply(lambda x:self.srcdir+x)

            if self.loclist is not None:
                mask = dnfiles['loc'].isin(self.loclist)
                dnfiles = dnfiles[mask].reset_index(drop=True)

            return dnfiles

        if self.srctype=='json':

            files = aq.listdir(self.srcdir, filetype='json')

            jsf = pd.DataFrame({"file":files})
            jsf["series"]= jsf["file"].apply(lambda x:x.split('.')[0])
            jsf["loc"] = jsf["series"].apply(lambda x:x.split('_')[0])
            jsf["fil"] = jsf["series"].apply(
                         lambda x:x.split('_')[-1].lstrip("0"))

            jsf["path"]= jsf['file'].apply(lambda x:os.path.join(
                                                    self.srcdir,x))

            if self.loclist is not None:
                mask = jsf['loc'].isin(self.loclist)
                jsf = jsf[mask].reset_index(drop=True)

            return jsf


    def gwseries(self,srname):
        """ Return single named GwSeries object from list

        Parameters
        ----------
        srname : str
            series name of requested GwSeries object

        Returns
        -------
        acequia.GwSeries object
        """

        if self.srctype in ['dinocsv','json']:
            row = self._flist[self._flist['series']==srname]
            indexval = row.index.values[0]
            filepath = self._flist.loc[indexval,'path']

        if self.srctype=='json':
            gw = aq.GwSeries.from_json(filepath)

        if self.srctype=='dinocsv':
            gw = aq.GwSeries.from_dinogws(filepath)

        if self.srctype=='hymon':
            for gw in self.hm:
                if gw.name==srname:
                    break

        return gw


