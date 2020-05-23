
import os
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

import acequia as aq


if __name__ == '__main__':

    listgws = 0

    if 1: 

        print()
        msg = 'test GwList from directory with dinocsv files'
        print(msg)
        print('-'*len(msg))

        sourcedir = r'.\testdata\dinogws\\'
        gwl = aq.GwList(srcdir=sourcedir,srctype='dinocsv')
        gwl.flist.to_csv(r'.\output\dinocsv_sourcefiles.csv',index=False)

        print(f'GwList with {len(gwl)} GwSeries has been created.')
        if listgws:
            for i,gw in enumerate(gwl):
                print(i,gw)
        print()

    if 1:

        msg = 'test GwList from direcetory with json files'
        print(msg)
        print('-'*len(msg))  

        sourcedir = r'.\output\json\\'
        gwl = aq.GwList(srcdir=sourcedir,srctype='json')
        gwl.flist.to_csv(r'.\output\json_sourcefiles.csv',index=False)

        print(f'GwList with {len(gwl)} GwSeries has been created.')
        if listgws:
            for i,gw in enumerate(gwl):
                print(i,gw)
        print()

    if 1:

        msg = 'test GwList with file with list of dinocsv files'
        print(msg)
        print('-'*len(msg))

        sourcepath = r'.\output\dinocsv_sourcefiles.csv'
        gwl = aq.GwList(srcfile=sourcepath,srctype='dinocsv')

        print(f'GwList with {len(gwl)} GwSeries has been created.')
        if listgws:
            for i,gw in enumerate(gwl):
                print(i,gw)
        print()

    if 1:

        msg = 'test GwList with file with list of json files'
        print(msg)
        print('-'*len(msg))

        sourcepath = r'.\output\json_sourcefiles.csv'
        gwl = aq.GwList(srcfile=sourcepath,srctype='json')

        print(f'GwList with {len(gwl)} GwSeries has been created.')
        if listgws:
            for i,gw in enumerate(gwl):
                print(i,gw)
        print()

    if 1:

        msg = 'test GwList from hydromonitor csv file'
        print(msg)
        print('-'*len(msg))

        srcdir = r'.\testdata\hydromonitor\\'
        fname = 'hydromonitor_testdata.csv'
        srcfile = os.path.join(srcdir,fname)
        gwhy = aq.GwList(srcfile=srcfile,srctype='hymon')

        print(f'GwList with {len(gwhy)} GwSeries objects has been created.')
        print()

        print(f'Test next() with HydroMonitor source')
        #if listgws:
        for gw in gwhy:
            print(gw)
        print()


    if 1:

        msg = 'test function headsfiles()'
        print(msg)
        print('-'*len(msg))

        sourcedir = r'.\output\json\\'
        flj = aq.headsfiles(sourcedir,'json')
        print(f'List with {len(flj)} sourcefilenames of type \'json\' has been created.')

        jloc = set(flj['loc'].values[:9])
        flj2 = aq.headsfiles(sourcedir,'json',jloc)
        print(f'List with {len(flj2)} sourcefilenames of type \'json\' has been created.')

        sourcedir = r'.\testdata\dinogws\\'
        fld = aq.headsfiles(sourcedir,'dinocsv')
        print(f'List with {len(fld)} sourcefilenames of type \'dinocsv\' has been created.')

        dloc = set(fld['loc'].values[:9])
        fld2 = aq.headsfiles(sourcedir,'dinocsv',dloc)
        print(f'List with {len(fld2)} sourcefilenames of type \'dinocsv\' has been created.')


        print()
