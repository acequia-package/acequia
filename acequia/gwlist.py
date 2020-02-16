

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

class GwList():
    """
        Iterator for list of GwSeries objects
    """

    def __repr__(self):
        return (f'{self.__class__.__name__}()')


    def __init__(self,srcdir=None,srctype='dinocsv',srclist=None,
        srcfile=None):
        """Create iterator for list of GwSeries objects  

        Variables
        ---------
        sourcedir : str, optional
            directory with groundwater level sourcefiles
        sourcetype : str
            type of sourcefiles in sourcedir ('dinocsv' or 'json')
        srclist : str, optional
            path to csv file with sourcefile names
        srcfile : str, optional
            path to csv sourcefile with grounwater measurements
            (only implemented for HydroMonitor csv export files)

        Examples
        --------
        
        Loading sourcefiles:
        gwsr = GwList(srcdir=<sourcedir>,srctype='dinocsv')
        gwsr = GwList(srcdir=<sourcedir>,srctype='json')
        gwsr = GwList(srfile=<hydromonitor csv export>,srctype='hymon')

        Printing string repr of al GwSeries objects:
        for i,gw in enumerate(gwsr):
            print(i,gw)


        """

        if srctype not in ['dinocsv','json','hymon']:
            raise ValueError(f'Given sourcetype \'{sourcetype}\' '+
                             f'is invalid. Valid values are '+
                             f'\'dinocsv\' or \'json\'.')
        else:
            self.srctype = srctype

        if srcdir is not None:
            if not os.path.isdir(srcdir):
                raise ValueError(f'Directory {sourcedir} does not exist')

        if srctype in ['dinocsv','json']:
            self.flist = self.filelist(srcdir=srcdir,srctype=srctype,
                         srclist=srclist)

        if srctype in ['hymon']:
            hm = aq.HydroMonitor.from_csv(filepath=srcfile)
            self.gwlist = hm.to_list()

        self.itercount = 0


    def __iter__(self):
        """ return GwList iterator """
        return self


    def __next__(self):
        """ return next gwseries object in list """
        
        if self.itercount >= self.__len__():
            raise StopIteration

        if self.srctype == 'dinocsv':
            filename = self.flist.at[self.itercount,'path']
            self.gw = aq.GwSeries.from_dinogws(filename)
        elif self.srctype == 'json':
            filename = self.flist.at[self.itercount,'path']
            self.gw = aq.GwSeries.from_json(filename)
        elif self.srctype == 'hymon':
            self.gw = self.gwlist[self.itercount]

        self.itercount += 1

        return self.gw


    def _list_dinocsv(self,srcdir):
        """ return list of dino sourcefiles in directory dir"""

        files = [f for f in os.listdir(srcdir) if os.path.isfile(
                 os.path.join(srcdir,f)) and f.split('.')[1]=='csv'
                 and f[11:13]=="_1"]

        # create dataframe
        dnfiles = DataFrame({"file":files})
        dnfiles["loc"] = dnfiles["file"].apply(lambda x:x[0:8])
        dnfiles["fil"] = dnfiles["file"].apply(
                                    lambda x:x[8:11].lstrip("0"))
        dnfiles["kaartblad"] = dnfiles["loc"].apply(lambda x:x[1:4])
        dnfiles["series"]= dnfiles["loc"]+"_"+dnfiles["fil"]
        dnfiles["path"]= dnfiles["file"].apply(lambda x:srcdir+x)

        return dnfiles


    def _list_json(self,srcdir):
        """ Return list of JSON sourcefiles in directory dir """

        files = [f for f in os.listdir(srcdir) if os.path.isfile(
                 os.path.join(srcdir,f)) and f.split('.')[1]=='json']

        # create dataframe
        jsf = DataFrame({"file":files})
        jsf["series"]= jsf["file"].apply(lambda x:x.split('.')[0])
        jsf["loc"] = jsf["series"].apply(lambda x:x.split('_')[0])
        jsf["fil"] = jsf["series"].apply(
                     lambda x:x.split('_')[-1].lstrip("0"))

        jsf["path"]= jsf['file'].apply(lambda x:os.path.join(srcdir,x))

        return jsf


    def filelist(self,srcdir=None,srctype='dinocsv',srclist=None):
        """ return pandas dataframe with sourcefile names 

        Variables
        ---------
        sourcedir : str, optional
            directory with groundwater level sourcefiles
        sourcetype : str
            type of sourcefiles in sourcedir ('dinocsv' or 'json')
        idxpath : str, optional
            path to csv file with sourcefile names

        When srcdir is given, list of sourcefiles will be made from
        this directory, depending on the value of parameter srctype.
        
        If parameter idxpath is given, list of sourcefiles will read
        from this file. When parameter srcdir is given, idxpath will
        be ignored.

        """

        if srcdir is None and srclist is None:
            raise ValueError('At least one of parameters srcdir or '
                            +'idpath must be given.')

        if srcdir is not None:

            if srctype=='dinocsv':
                flist = self._list_dinocsv(srcdir)

            if srctype=='json':
                flist = self._list_json(srcdir)

        if srcdir is None and srclist is not None:

            if not os.path.exists(srclist):
                raise ValueError(f'Filepath {srclist} does not exist.')

            ftime = datetime.fromtimestamp(os.path.getmtime(srclist))
            fileage = datetime.now()-ftime
            if fileage.days > 1:
                logger.warning(
                f'Age of {srclist} is {fileage.days} days.')

            flist = pd.read_csv(srclist,index_col=False)

        return flist


    def __len__(self):
        """ return number of GwSeries objects """
        if self.srctype in ['dinocsv','json']:
            return len(self.flist)
        elif self.srctype in ['hymon']:
            return len(self.gwlist)
