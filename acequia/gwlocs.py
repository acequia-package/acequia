

""" This module contains the object GwLocs


"""

import os
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


class GwLocs:
    """Manage multiple groundwater heads series from one well location

    Parameters
    ----------
    filedir : str
        directory with source files

    filelist : list, optional
        list of sourcefile names (without path)

    filetype : ['.csv','.json'], optional
        source file type 

    groups : list, optional
        list of location names, sublists are allowed (see examples)

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
        """ """
        self._filedir = filedir
        self._pathlist = pathlist
        self._filetype = filetype
        self._groups = groups

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

        self._table = self._loctable()
        self._create_iterator()


    def __repr__(self):
        nlocs = len(self._table.groupby(by='loc').size())
        return (f'GwLocs(n={nlocs})')


    def _infer_filetype(self):
        """Infer filetype from file extensin count in <filedir>"""
        filelist = [os.path.basename(path) for path in self._pathlist]
        extlist = [os.path.splitext(filename)[1] for filename in filelist]
        sr = Series(extlist).value_counts()
        return sr.index[0]


    def _loctable(self):
        """List all files in filedir and return well locations table"""
        if self._filetype=='.json':
            filepaths = [x for x in self._pathlist]
            filenames = [os.path.basename(path) for path in self._pathlist]
            filetypes = [os.path.splitext(name)[1] for name in filenames]
            series = [os.path.splitext(name)[0] for name in filenames]
            locations = [x.split('_')[0] for x in series]
            filters = [x.split('_')[1] for x in series]

        if self._filetype=='.csv':
            # dino zipfiles come with two files for each filter
            # only files ending with _1.csv are needed
            # filename: B01C0008001_1.csv
            filepaths = [x for x in self._pathlist if x.endswith('_1.csv')]
            filenames = [os.path.basename(x) for x in filepaths]
            filetypes = [os.path.splitext(name)[1] for name in filenames]
            locations = [x[:8] for x in filenames]
            filters = [x[8:11].lstrip('0') for x in filenames]
            series = [x[0]+'_'+x[1] for x in list(zip(locations,filters))]

        table = DataFrame(data={
                'loc':locations,
                'fil':filters,
                'filename':filenames,
                'filetype':filetypes,
                'filepaths':filepaths,
                },index=series)
        table.index.name = 'series'
        return table


    def _create_iterator(self):
        """Create location series groups iterator """
        self._itercount = 0
        if self._groups is None:
            grp = self._table.groupby(by='loc')
            self._grpnames = list(grp.groups.keys())
        else:
            self._grpnames = self._groups
            #todo: check if groupnames are in table


    def loctable(self,filedir=None):
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
            return self._table

        if not os.path.isdir(filedir):
            msg = f'{filedir} must be a valid directory'
            raise ValueError(msg)

        return self._loctable(filedir)


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

        mask = self._table['loc'].isin(loc)
        for i,(srname,row) in enumerate(self._table[mask].iterrows()):

            filepath = os.path.join(self._filedir,row['filename'])
            if self._filetype=='.json':
                gw = aq.GwSeries.from_json(filepath)
            if self._filetype=='.csv':
                gw = aq.GwSeries.from_dinogws(filepath)

            if i==0:
                gwlist = [gw]
            else:
                gwlist.append(gw)

        return gwlist


    def __iter__(self):
        return self


    def __len__(self):
        return len(self._grpnames)


    def __next__(self):

        if self._itercount >= len(self):
            raise StopIteration

        loc = self._grpnames[self._itercount]
        mygwlist = self.gwseries(loc=loc)

        self._itercount+=1
        return mygwlist

