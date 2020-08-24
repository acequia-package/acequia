

import os

from pandas import Series, DataFrame
import pandas as pd

#import acequia as aq
#from gwlocs import GwLocs
from acequia import GwLocs

if __name__ == '__main__':


    # test invalid input
    try:
        notastring = ['list item']
        locs = GwLocs(notastring)
    except Exception as ex:
        print(ex)

    try:
        invalidir = '.\\justaname\\'
        locs = GwLocs(invalidir)
    except Exception as ex:
        print(ex)

    # test init
    dinodir = '.\\testdata\\dinogws\\'
    locs = GwLocs(filedir=dinodir)
    print(locs)

    jsondir = '.\\testdata\\json\\'
    locs = GwLocs(filedir=jsondir)
    print(locs)

    # test loctable()
    tbl1 = locs.loctable()
    print(len(tbl1))

    # test _inder_filetype()
    ftype = locs._infer_filetype(jsondir)
    print(f'Inferred filetype is {ftype}')

    # test loctable()
    tbl2 = locs.loctable(jsondir)
    print(len(tbl2))

    # test gwseries(loc)
    names = ['B21A0138','B21G1057','B22B0226','B24H0080','B29A0850']
    gwlist = locs.gwseries(loc=names)

    # test iterator on directory (valid files only)
    locs = GwLocs(filedir=jsondir,groups=names)
    for i in range(len(locs)):
        gws = next(locs)
        print(f'{names[i]} group size is {len(gws)}')
    print()

    # test iterator on list of names (valid files only)
    names = ['B21A0138','B21G1057',['B22B0226','B24H0080'],'B29A0850']
    locs = GwLocs(filedir=jsondir,groups=names)
    for i in range(len(locs)):
        gws = next(locs)
        print(f'{names[i]} group size is {len(gws)}')
    print()

    for loc in GwLocs(filedir=jsondir,groups=names):
        print(f'{names[i]} group size is {len(gws)}')
    print()

    # test iterator on directory (some empty files)
    jsondir = '.\\testdata\\json_some_empty\\'
    locs = GwLocs(filedir=jsondir,groups=names)
    for i in range(len(locs)):
        gws = next(locs)
        print(f'{names[i]} group size is {len(gws)}')
    print()

