


import acequia as aq


if __name__ == '__main__':


    # load GwSeries for testing
    sourcedir = ".\\testdata\\dinogws\\"
    srcfile = "B28A0475002_1.csv"
    gw = aq.GwSeries.from_dinogws(sourcedir+srcfile)
    ts = gw.heads(ref='datum')

    # test hydroyear
    hdr = aq.hydroyear(ts)

    # test season
    seas = aq.season(ts)

    # test .stats.utils index1428
    years = set(ts.index.year)
    idx = aq.index1428(minyear=min(years),maxyear=max(years),days=[14,28])

    # test .stats.utils heads1428
    ts1428 = aq.ts1428(ts,maxlag=3)

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
