

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

    mfrq = aq.measurement_frequency(sr)
    maxfrq = aq.max_frequency(sr)

    gxg = aq.GxgStats(gw)
    vg1 = gxg.vg1()
    vg3 = gxg.vg3()
    xg = gxg.xg()
    gxgtbl = gxg.gxg()

    gxgmv = aq.GxgStats(gw,ref='surface')
    sr1 = Series(name='gxg',dtype='object')
    sr1['GHG'] = gxgmv.ghg()
    sr1['GLG'] = gxgmv.glg()
    sr1['GT'] = gxgmv.gt()
    sr1['V89pol'] = gxgmv.gvg_approx('VDS89pol')
    sr1['V89sto'] = gxgmv.gvg_approx('VDS89sto')
    sr1['RUNH'] = gxgmv.gvg_approx('RUNHAAR')

    vg1mv = gxgmv.vg1()
    vg3mv = gxgmv.vg3()
    xgmv = gxgmv.xg()
    gxgtblmv = gxgmv.gxg()

    


    if 0:

        gwl = GwList(srcdir=srcdir)
        for i,gw in enumerate(gwl):
            if 1<10:
                print(i,gw)


