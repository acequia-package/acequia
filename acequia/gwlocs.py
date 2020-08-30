

""" This module contains the object GwLocs
dsDif


"""

import os
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq


class GwLocs:
    """Manage multiple series from one well location

    Parameters
    ----------
    filedir : str
        directory with source files

    Examples
    --------
    Basic commands:
    >>>locs = GwLocs(filedir=<jsondir>)
    >>>tbl = locs.loctable()
    >>>gws = GwLocs.gwseries(loc='B16D0037')

    Return list of GwSeries objects for locations in list:
    >>>names = ['B16D0037','B27G0237',['B28D1635','B28B1388'],'B28B1389']
    >>>for loc in GwLocs(filedir=<jsondir>,groups=names3):
            print(f'{names3[i]} group size is {len(gws)}')

    Explicitly iterate over locations:
    >>>locs = GwLocs(filedir=<jsondir>,groups=names3)
    >>>for i in range(len(locs)):
            gws = next(locs)
            print(f'{names3[i]} group size is {len(gws)}')

    """

    def __init__(self,filedir=None,filetype=None,groups=None):

        if not isinstance(filedir,str):

            msg = f'{filedir} is not a string'
            raise ValueError(msg)

        if not os.path.isdir(filedir):

            msg = f'{filedir} is not a valid directory'
            raise ValueError(msg)

        if filetype is None:
            filetype = self._infer_filetype(filedir)

        if filetype not in ['json','csv']:
            msg = f'Unsupported filetype {filetype}.'
            raise ValueError(msg)

        self.filedir = filedir
        self._filetype = filetype
        self.table = self.loctable(self.filedir)

        # prepare iterator
        self._itercount = 0
        if groups is None:
            grp = self.table.groupby(by='loc')
            self._grpnames = list(grp.groups.keys())
        else:
            self._grpnames = groups
            #todo: check is groupnames are in table


    def __repr__(self):
        nlocs = len(self.table.groupby(by='loc').size())
        return (f'GwLocs(n={nlocs})')


    def _infer_filetype(self,filedir):
        """Infer filetype from file extensin count in <filedir>"""

        extlist = [f.split('.')[1] for f in os.listdir(filedir)
                   if os.path.isfile(os.path.join(filedir,f))]
        extdict = {x:extlist.count(x) for x in extlist}
        return max(extdict, key=extdict.get)


    def _loctable(self,filedir):
        """List all files in filedir and return well locations table"""

        filenames = [f for f in os.listdir(filedir)
                     if os.path.isfile(os.path.join(filedir,f)) 
                    ]

        if self._filetype=='json':
            filetype = [x.split('.')[1] for x in filenames]
            locations = [x.split('_')[0] for x in filenames]
            filters = [x.split('_')[1] for x in filenames]
            series = [x.split('.')[0] for x in filenames]

        if self._filetype=='csv':
            # dino zipfiles come with two files for each filter
            # only files ending with _1.csv are needed
            filenames = [x for x in filenames if x[-6:]=='_1.csv']

            filetype = [x.split('.')[1] for x in filenames]
            locations = [x[:8] for x in filenames]
            filters = [x[8:11].lstrip('0') for x in filenames]
            series = [x[0]+'_'+x[1] for x in list(zip(locations,filters))]

        table = DataFrame(data={
                'loc':locations,
                'fil':filters,
                'filename':filenames,
                'filetype':filetype,
                },index=series)
        table.index.name = 'series'
            
        return table


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
            return self.table

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

        mask = self.table['loc'].isin(loc)
        for i,(srname,row) in enumerate(self.table[mask].iterrows()):

            filepath = os.path.join(self.filedir,row['filename'])
            if self._filetype=='json':
                gw = aq.GwSeries.from_json(filepath)
            if self._filetype=='csv':
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

