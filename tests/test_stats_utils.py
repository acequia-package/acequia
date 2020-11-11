


import acequia as aq


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

# test gxg statistics

gxgstat = aq.Gxg(ts,srname=gw.name())
vg3 = gxgstat.vg3()
vg1 = gxgstat.vg1()
xg3 = gxgstat.xg3()
xg3tbl = gxgstat.xg3table()

gxg = gxgstat.gxgtable()
