

"""
    Test stats.Describe object 

"""

import acequia as aq

def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':

    srcdir = r'.\testdata\dinogws_smalltest\\'
    outdir = r'.\output\tables\\'

    fpath = f'{srcdir}B29A0016001_1.csv'
    gw = aq.GwSeries.from_dinogws(fpath)


    hdr('test self._create_list()')
    ds = aq.GwListStats(srcdir)
    gws = ds._create_list()

    hdr('test self._table_series()')
    ds = aq.GwListStats(srcdir)
    tbl1 = ds._table_series()

    hdr('# test self.timestatstable(gxg=False) ')
    ds = aq.GwListStats(srcdir)
    tbl2 = ds.timestatstable(gxg=False)

    hdr('# test self.timestatstable(gxg=True) ')
    ds = aq.GwListStats(srcdir)
    tbl3 = ds.timestatstable(gxg=True)

    hdr('# test custom function aq.gwliststats(gxg=False)')
    tbl4 = aq.gwliststats(srcdir, gxg=False)

    hdr('# test custom function aq.gwliststats(gxg=True)')
    tbl5 = aq.gwliststats(srcdir, gxg=True, ref='surface')

    hdr('# test custom function aq.gwlocstats() ')
    tbl6 = aq.gwlocstats(tbl4)



