

""" This module contains the object GwLocs


"""

import os
import warnings
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


class GwLocs:
    """Manage multiple groundwater heads series from one well location


    Methods
    -------
    loctable(self,filedir=None)
        return list of location and heads series names

    gwseries(self,loc=None)
        return list of GwSeries objects

    Examples
    --------
    Create GwLocs object:
    >>>locs = GwLocs(filedir=<jsondir>)

    Return table of locations and series:
    >>>tbl = locs.loctable()

    Return al series for location B16D0037:
    >>>gws = GwLocs.gwseries(loc='B16D0037')

    Return list of GwSeries objects for locations in list:
    >>>names = ['B16D0037','B27G0237',['B28D1635','B28B1388'],'B28B1389']
    >>>for loc in GwLocs(filedir=<jsondir>,groups=names):
            print(f'{names[i]} group size is {len(gws)}')

    Explicitly iterate over locations:
    >>>locs = GwLocs(filedir=<jsondir>,groups=names)
    >>>for i in range(len(locs)):
            gws = next(locs)
            print(f'{names[i]} group size is {len(gws)}')
    """

    def __init__(self,filedir=None,pathlist=None,filetype=None,
        groups=None):
        """ 
        Parameters
        ----------
        filedir : str
            directory with source files

        pathlist : list, optional
            list of sourcefile names (without path)

        filetype : ['.csv','.json'], optional
            source file type 

        groups : list, optional
            list of location names, sublists are allowed (see examples)
        """

        self._filedir = filedir
        self._pathlist = pathlist
        self._filetype = filetype
        self._loclist = groups

        if not isinstance(self._filedir,str):
            msg = f'filedir must be a string, not {self._filedir}'
            raise ValueError(msg)

        if not os.path.isdir(self._filedir):
            msg = f'{self._filedir} is not a valid directory'
            raise ValueError(msg)

        if self._pathlist is None:
            self._pathlist = aq.listdir(dirpath=self._filedir)

        if self._filetype is None:
            self._filetype = self._infer_filetype()

        if self._filetype in ['json','csv']:
            self._filetype = '.'+self._filetype

        if self._filetype not in ['.json','.csv']:
            msg = f'Unsupported filetype {filetype}.'
            raise ValueError(msg)

        self._srcfiles = self._list_sourcefiles()
        self._locfiles = self.list_locfiles()
        self._create_iterator()


    def __repr__(self):
        nlocs = len(self._locfiles.groupby(by='loc').size())
        nseries = len(self._locfiles)
        return (f'GwLocs(nlocs={nlocs})')


    def _infer_filetype(self):
        """Infer filetype from file extensin count in <filedir>"""
        filelist = [os.path.basename(path) for path in self._pathlist]
        extlist = [os.path.splitext(filename)[1] for filename in filelist]
        sr = Series(extlist).value_counts()
        return sr.index[0]


    def _list_sourcefiles(self):
        """List all valid source files in filedir and return table"""
        if self._filetype=='.json':
            filepaths = [x for x in self._pathlist]
            fnames = [os.path.basename(path) for path in self._pathlist]
            ftypes = [os.path.splitext(name)[1] for name in fnames]
            series = [os.path.splitext(name)[0] for name in fnames]
            locations = [x.split('_')[0] for x in series]
            filters = [x.split('_')[1] for x in series]

        if self._filetype=='.csv':
            # dino zipfiles come with two files for each filter
            # only files ending with _1.csv are needed
            # filename: B01C0008001_1.csv
            filepaths = [x for x in self._pathlist if x.endswith('_1.csv')]
            fnames = [os.path.basename(x) for x in filepaths]
            ftypes = [os.path.splitext(name)[1] for name in fnames]
            locations = [x[:8] for x in fnames]
            filters = [x[8:11].lstrip('0') for x in fnames]
            series = [x[0]+'_'+x[1] for x in list(zip(locations,filters))]

        table = DataFrame(data={
                'loc':locations,
                'fil':filters,
                'filename':fnames,
                'filetype':ftypes,
                'filepaths':filepaths,
                },index=series)
        table.index.name = 'series'
        return table


    def list_sourcefiles(self,filedir=None):
        """Return table with list of series names and well location 
        names based on sourcefile names in directory filedir

        Parameters
        ----------
        filedir : str, optional
            directory with sourcefile names

        Returns
        -------
        pd.DataFrame

        Notes
        -----
        Directory <filedir> should contain source files with filenames
        composed of <location name>_<filter>.<extension>, like in 
        'B28H0025_1.csv' or 'Mylocation_Myfilter.json'.

        """

        if filedir is None:
            return self._srcfiles

        if not os.path.isdir(filedir):
            msg = f'{filedir} must be a valid directory'
            raise ValueError(msg)

        return self._list_sourcefiles(filedir)


    def list_locfiles(self):
        """List source files for all locations"""

        def flatten_nested_list(nested_list):
            # stackoverflow.com/questions/10823877/
            for i in nested_list:
                if isinstance(i, (list,tuple)):
                    for j in flatten_nested_list(i):
                        yield j
                else:
                    yield i

        if self._loclist is not None:
            flatlist = flatten_nested_list(self._loclist)
            mask = self._srcfiles['loc'].isin(flatlist)
            srcloc = self._srcfiles[mask]
        else:
            srcloc = self._srcfiles

        if srcloc.empty:
            msg = f'list_locfiles returns empty dataframe.'
            warnings.warn(msg)

        return srcloc

    def _create_iterator(self):
        """Create location series groups iterator """
        self._itercount = 0
        if self._loclist is None:
            ##grp = self._srcfiles.groupby(by='loc')
            grp = self._locfiles.groupby(by='loc')
            self._loclist = list(grp.groups.keys())
        else:
            self._loclist = self._loclist
            #todo: check if groupnames are in table


    def gwseries(self,loc=None):
        """Return list of GwSeries objects with location name <loc>

        Parameters
        ----------
        loc : str
            name of location

        Return
        ------
        list of GwSeries objects

        Notes
        -----
        When parameter loc is a list of locations names, GwSeries objects
        for all these locations will be returned.
        """

        if isinstance(loc,str):
            loc = [loc]

        gwlist = []
        mask = self._srcfiles['loc'].isin(loc)
        for i,(srname,row) in enumerate(self._srcfiles[mask].iterrows()):

            filepath = os.path.join(self._filedir,row['filename'])
            if self._filetype=='.json':
                gw = aq.GwSeries.from_json(filepath)
            if self._filetype=='.csv':
                gw = aq.GwSeries.from_dinogws(filepath)
            gwlist.append(gw)

        return gwlist


    def __iter__(self):
        return self


    def __len__(self):
        return len(self._loclist)


    def __next__(self):

        if self._itercount >= len(self):
            raise StopIteration

        loc = self._loclist[self._itercount]
        mygwlist = self.gwseries(loc=loc)

        self._itercount+=1
        return mygwlist

