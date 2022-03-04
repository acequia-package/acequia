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
newline = '\n'

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


    _valid_srctype = ['dinocsv','json','hymon','waterweb']

    def __repr__(self):
        mylen = len(self)
        return (f'{self.__class__.__name__}({mylen})')


    def __init__(self,srcdir=None,srctype='dinocsv',loclist=None,
        srcfile=None):
        """Return GwList object

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


        """

        self._srcdir = srcdir
        self._srctype = srctype
        self._loclist = loclist
        self._srcfile = srcfile
        self._itercount = 0


        if (self._srcdir is None) and (self._srcfile is None):
            raise ValueError((
                'missing parameter value'
                f'At least one of parameters srcdir or '
                f'srclist must be given.'))

        if self._srctype not in self._valid_srctype:
            raise ValueError((
                'srctype value not recognised.\n'
                f'"{self._srctype}" is not a valid '
                f'sourcefile type. Valid sourcefiletypes are '
                f'{self._valid_srctype}'))

        if (self._srcdir is not None) and (self._srcfile is not None):
            self._srcfile = None # given value for srcfile is ignored!
            warnings.warn((
                'Ambigious combination of parameter values:\n'
                f'srcdir is {self._srcdir} (not None) and srcfile is '
                f'{self._srcfile} (not None). Given value for srcfile '
                f'will be ignored.'))

        if self._srcdir is not None:

            if not os.path.isdir(self._srcdir):
                raise ValueError(f'Directory {self._srcdir} does not exist')

            self._flist = self.filetable() #_sourcefiles()


        if (self._srcfile is not None) and (
            self._srctype in ['dinocsv','json']):

            if not os.path.exists(self._srcfile):
                raise ValueError(f'Filepath {self._srcfile} does not exist.')

            self._flist = self.filetable()

        if (self._srcfile is not None) and (self._srctype=='hymon'):
            self.hm = aq.HydroMonitor.from_csv(filepath=srcfile)

        if (self._srcfile is not None) and (self._srctype=='waterweb'):
            self._wwn = aq.WaterWeb.from_csv(srcfile,networkname=None)


    def filetable(self):
        """ Return list of sourcefile names """

        if (self._srcdir is not None) and (self._srctype 
                in ['dinocsv','json']):

            return self._sourcefiles()

        if (self._srcfile is not None) and (self._srctype in ['dinocsv','json']):

            ftime = datetime.fromtimestamp(os.path.getmtime(self._srcfile))
            fileage = datetime.now()-ftime
            if fileage.days > 1:
                msg = f'Age of {self._srcfile} is {fileage.days} days.' 
                warnings.warn(msg)

            #TODO: check if flist contains valid sourcefilenames

            ## flist must be a list of sourcefilesnames
            flist = pd.read_csv(self._srcfile,index_col=False)

            return flist

        if (self._srcfile is not None) and (self._srctype=='hymon'):
            msg = ' '.join([
                f'function filelist() not supported for sourcetype',
                f'\'hymon\' ',])
            warnings.warn(msg)
            ##logger.warning(msg)
            return None

        warnings.warn((f'Unexpected combination of given parameters. ')
            (f'No list of GwSeries objects is returned.'))
        ##logger.warning(msg)
        return None


    def __iter__(self):
        """ return iterator """
        return self


    def __next__(self):
        """ return next gwseries object in list """
        
        if self._itercount >= self.__len__():
            self._itercount = 0
            raise StopIteration

        if self._srctype == 'dinocsv':
            idx = self._flist.index[self._itercount]
            filename = self._flist.at[self._itercount,'path']
            self.gw = aq.GwSeries.from_dinogws(filename)
 
        if self._srctype == 'json':
            idx = self._flist.index[self._itercount]
            filename = self._flist.at[idx,'path']
            self.gw = aq.GwSeries.from_json(filename)

        if self._srctype == 'hymon':
            self.gw = next(self.hm)

        if self._srctype == 'waterweb': 
            srname = self._wwn.srnames()[self._itercount]
            self.gw = self._wwn.gwseries(srname)

        self._itercount += 1
        return self.gw

   
    def __len__(self):

        if self._srctype in ['dinocsv','json']:
            return len(self._flist)

        if self._srctype in ['hymon']:
            return len(self.hm)

        if self._srctype=='waterweb':
            return len(self._wwn)


    def is_callable(self):
        """Return True if object is waiting for a call"""

        if self._itercount==0:
            is_callable = True
        else:
            is_callable = False
        return is_callable


    def _sourcefiles(self):
        """ return list of sourcefiles in directory dir"""

        if self._srctype=='dinocsv':

            pathlist = aq.listdir(self._srcdir, filetype='csv')
            filelist = [os.path.split(path)[-1] for path in pathlist if path.split('_')[-1].endswith('1.csv')]
            dnfiles = pd.DataFrame({"file":filelist})

            dnfiles["loc"] = dnfiles["file"].apply(lambda x:x[0:8])
            dnfiles["fil"] = dnfiles["file"].apply(
                lambda x:x[8:11].lstrip("0"))
            dnfiles["kaartblad"] = dnfiles["loc"].apply(lambda x:x[1:4])
            dnfiles["series"]= dnfiles["loc"]+"_"+dnfiles["fil"]
            dnfiles["path"]= dnfiles["file"].apply(lambda x:self._srcdir+x)

            if self._loclist is not None:
                mask = dnfiles['loc'].isin(self._loclist)
                dnfiles = dnfiles[mask].reset_index(drop=True)

            return dnfiles

        if self._srctype=='json':

            files = aq.listdir(self._srcdir, filetype='json')

            jsf = pd.DataFrame({"file":files})
            jsf["series"]= jsf["file"].apply(lambda x:x.split('.')[0])
            jsf["loc"] = jsf["series"].apply(lambda x:x.split('_')[0])
            jsf["fil"] = jsf["series"].apply(
                         lambda x:x.split('_')[-1].lstrip("0"))

            jsf["path"]= jsf['file'].apply(lambda x:os.path.join(
                                                    self._srcdir,x))

            if self._loclist is not None:
                mask = jsf['loc'].isin(self._loclist)
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

        if self._srctype in ['dinocsv','json']:
            row = self._flist[self._flist['series']==srname]
            indexval = row.index.values[0]
            filepath = self._flist.loc[indexval,'path']

        if self._srctype=='json':
            gw = aq.GwSeries.from_json(filepath)

        if self._srctype=='dinocsv':
            gw = aq.GwSeries.from_dinogws(filepath)

        if self._srctype=='hymon':
            for gw in self.hm:
                if gw.name==srname:
                    break

        if self._srctype=='waterweb':
            gw = self._wwn.gwseries(srname)

        return gw


