

import os

from pandas import Series, DataFrame
import pandas as pd

from acequia import GwLocs
import acequia as aq



if __name__ == '__main__':


    if 0:
        # test invalid location input
        try:
            notastring = ['list item']
            locs = GwLocs(notastring)
        except Exception as ex:
            print(ex)

        # test invalid directory name input
        try:
            invalidir = '.\\justaname\\'
            locs = GwLocs(invalidir)
        except Exception as ex:
            print(ex)

    if 0:

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
        ftype = locs._infer_filetype()
        print(f'Inferred filetype is {ftype}')

        # test loctable()
        tbl2 = locs.loctable()
        print(len(tbl2))

        # test gwseries(loc)
        names = ['B21A0138','B21G1057','B22B0226','B24H0080','B29A0850']
        gwlist = locs.gwseries(loc=names)

    if 0:

        # test iterator on directory (valid files only)
        locs = GwLocs(filedir=jsondir,groups=names)
        for i in range(len(locs)):
            gws = next(locs)
            print(f'{names[i]} number of series is {len(gws)}')
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

    if 0:

        # test GwLocs.init with given filelist
        dirpath = '.\\testdata\\dinogws\\'
        ##dirpath = 'D:\\py3\\gwdata\\dino2020\\'
        filepath = '.\\temp\\filelist.csv'

        filelist =  aq.listdir(dirpath)
        #pd.Series(filelist).to_csv(filepath,index=False,header=False)

        #df = pd.read_csv(filepath,header=None,names=['filename'])
        #filelist = df['filename'].tolist()

        locs = GwLocs(filedir=dirpath,pathlist=filelist,filetype='.csv')
        print(f'locs : {locs}')

    if 1:

        dirpath = '.\\testdata\\dinogws\\'
        names = ['B34D0081','B34D0082','B34D0083']
        names = ['B21A0138','B21G1057',['B22B0226','B24H0080'],'B29A0850',
                 'NOTVALID']
        locs = GwLocs(filedir=dirpath,filetype='.csv',groups=names)
        print(f'locs : {locs}')
