
import os
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

import acequia as aq


if __name__ == '__main__':

    if 1: # test GwList from directory with dinocsv files

        sourcedir = r'.\testdata\dinogws\\'
        gwsr = aq.GwList(srcdir=sourcedir,srctype='dinocsv')
        gwsr.flist.to_csv(r'.\output\dinocsv_sourcefiles.csv',index=False)
        for i,gw in enumerate(gwsr):
            print(i,gw)

    if 1: # test GwList from direcetory with json files

        sourcedir = r'.\output\json\\'
        gwsr = aq.GwList(srcdir=sourcedir,srctype='json')
        gwsr.flist.to_csv(r'.\output\json_sourcefiles.csv',index=False)
        for i,gw in enumerate(gwsr):
            print(i,gw)
        print()

    if 1: # test GwList from indexfile of dinocsv files
    
        sourcepath = r'.\output\dinocsv_sourcefiles.csv'
        gwsr = aq.GwList(srclist=sourcepath,srctype='dinocsv')
        for i,gw in enumerate(gwsr):
            print(i,gw)
        print()

    if 1: # test GwList from indexfile of json files
    
        sourcepath = r'.\output\json_sourcefiles.csv'
        gwsr = aq.GwList(srclist=sourcepath,srctype='json')
        for i,gw in enumerate(gwsr):
            print(i,gw)
        print()

    if 1:

        srcdir = r'.\testdata\hydromonitor\\'
        fname = 'hydromonitor_testdata.csv'
        srcfile = os.path.join(srcdir,fname)

        gwsr = aq.GwList(srcfile=srcfile,srctype='hymon')
        for i,gw in enumerate(gwsr):
            print(i,gw)
        print()
