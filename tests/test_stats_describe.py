

"""
    Test stats.Describe object 

"""

import acequia as aq


if __name__ == '__main__':

    srcdir = r'.\testdata\dinogws\\'
    outdir = r'.\output\tables\\'

    # test _create_list()
    ds = aq.Describe(srcdir)
    gws = ds._create_list()

    # test _table_series()
    ds = aq.Describe(srcdir)
    dfsr = ds._table_series()

    # test _table_locs()
    ds = aq.Describe(srcdir)
    dfloc = ds._table_locs()

    # test _table_timestatstable()
    ds = aq.Describe(srcdir)
    ds.timestatstable(locs=True)

    #  test custom function aq.describe()
    tbsr = aq.timestatstable(srcdir)
    tbloc = aq.timestatstable(srcdir,locs=True)

