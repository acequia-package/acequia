

"""
    Test GxG object 

"""

from pandas import Series, DataFrame
import pandas as pd
from acequia import GwSeries
from acequia import GxgStats
from acequia import GwList
import acequia as aq



if __name__ == '__main__':


    srcdir = r'D:\py3\package-acequia\acequia\tests\testdata\dinogws\\'
    srcfile = "B28A0475002_1.csv"
    gw = aq.GwSeries.from_dinogws(srcdir+srcfile)
    sr = gw.heads(ref='datum')

    gxg = aq.GxgStats(gw)
    gxgtbl = gxg.gxg()


    sr = Series(name='gxg',dtype='object')
    sr['GHG'] = gxg.ghg()
    sr['GLG'] = gxg.glg()

    vg1 = gxg.vg1()
    vg3 = gxg.vg3()

    sr['GT'] = gxg.gt()

    xg = gxg.xg()
    gxgmvtbl = gxg.gxg(reflev='surface')

    


    if 0:

        gwl = GwList(srcdir=srcdir)
        for i,gw in enumerate(gwl):
            if 1<10:
                print(i,gw)


