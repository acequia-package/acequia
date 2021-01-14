

"""
    Test stats.Describe object 

"""

import acequia as aq


if __name__ == '__main__':

    srcdir = r'.\testdata\dinogws\\'
    outdir = r'.\output\tables\\'

    # test _create_list()
    ds = aq.DescribeGwList(srcdir)
    gws = ds._create_list()

    # test _table_series()
    ds = aq.DescribeGwList(srcdir)
    dfsr = ds._table_series()

    # test _table_locs()
    ds = aq.DescribeGwList(srcdir)
    dfloc = ds._table_locs()

    # test _table_timestatstable()
    ds = aq.DescribeGwList(srcdir)
    tbl = ds.timestatstable(locs=True, gxg=True)

    #  test custom function aq.describe()
    tbsr = aq.timestatstable(srcdir,gxg=False)
    tbloc = aq.timestatstable(srcdir,locs=True)

    #  test custom function aq.describe() with GxG is True
    tbsr2 = aq.timestatstable(srcdir,gxg=True)
