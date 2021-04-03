


import acequia as aq


def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':


    hdr('# load GwSeries for testing')
    sourcedir = ".\\testdata\\dinogws\\"
    srcfile = "B28A0475002_1.csv"
    gw = aq.GwSeries.from_dinogws(sourcedir+srcfile)
    ts = gw.heads(ref='datum')

    print(gw)

    hdr('# test hydroyear')
    hydyear = aq.hydroyear(ts)
    print(hydyear)

    hdr('# test season')
    seas = aq.season(ts)
    print(set(seas))

    hdr('# test .stats.utils index1428')
    years = set(ts.index.year)
    idx = aq.index1428(minyear=min(years),maxyear=max(years),days=[14,28])
    print(idx[:4])

    hdr('# test .stats.utils heads1428')
    ts1428 = aq.ts1428(ts,maxlag=3)
    print(ts1428[:4])

    hdr('# test stats.utils.measfrqclass')
    classlist = [0,3,10,15,35]
    classlist = [aq.stats.utils.measfrqclass(x) for x in classlist]
    print(classlist)

    hdr('# test stats.utils.measfrq')
    msf = aq.measfrq(ts)
    print(msf[:4])

    hdr('# test stats.utils.maxfrq')
    mxf1 = aq.maxfrq(ts)
    print(f'test with time series of measured heads: {mxf1}')
    mxf2 = aq.maxfrq(aq.measfrq(ts))
    print(f'test with series of frequency classes for each year: {mxf2}')

    sr2 = aq.measfrq(ts)
    sr2[:] = ts.groupby(ts.index.year).count()
    mxf3 = aq.maxfrq(sr2)
    print(f'test with series number of measurements for each year: {mxf3}')

    maxf4 = aq.maxfrq(sr2.values)
    print((f'test with numpy array with number of measurements for'
        f'each year: {maxf4}'))

    maxf5 = aq.maxfrq(list(sr2.values))
    print((f'test with list with number of measurements for '
        f'each year: {maxf5}'))

    if 0:
        # test gxg statistics
        gxgstat = aq.Gxg(ts,srname=gw.name())
        vg3 = gxgstat.vg3()
        vg1 = gxgstat.vg1()
        xg = gxgstat.xg()
        gxg = gxgstat.gxg()

        # quantiles

        ts2 = gw.heads(ref='surface')
        qt = aq.Quantiles(ts2,srname=gw.name(),nclasses=20)
        qts = qt.table()
        ax = qt.plot(years=[1983],figname='duurlijnen.jpg')
