""" This module contains a class GwGxg that calculates some
descriptive statistics from a series of groundwater head measurements
used by groundwater practitioners in the Netherlands 

Author: Thomas de Meij (who borrowed lavishly from Pastas dutch.py)

"""

from datetime import datetime
import datetime as dt
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

import acequia as aq


class Gxg:
    """Calculate descriptive statistics from measured heads"""

    n14 = 18

    def __init__(self, ts, srname=None, ref='datum'):
        """
        Parameters
        ----------
        ts : pd.Series
            timeseries with groundwater head measurments

        ref : str, ['datum','surface']
            reference level for measurements

        """

        self.ts = ts
        self.ts1428 = aq.ts1428(ts,maxlag=3,remove_nans=False)
        self.ref = ref

        if srname is None: srname = 'series'
        self.srname = srname


    def vg3(self):
        """Return VG (Spring Level) calculateds as mean of groundwater 
        levels at 14 march, 28 march and 14 april"""

        for i,year in enumerate(set(self.ts1428.index.year)):
            v1 = self.ts1428[dt.datetime(year,3,14)]
            v2 = self.ts1428[dt.datetime(year,3,28)]
            v3 = self.ts1428[dt.datetime(year,4,14)]
            mean = round((v1+v2+v3)/3,2)

            if i==0:
                years = []
                vg3 = []
            years.append(year)
            vg3.append(mean)

        srvg3 = pd.Series(data=vg3,index=years)
        return srvg3


    def vg1(self,maxlag=7):
        """Return VG (Spring Level) calculated as measurement nearest
        to 1 april"""

        years = set(self.ts1428.index.year)
        srvg1 = pd.Series(data=np.nan,index=years)

        for i,year in enumerate(srvg1.index):

            date = dt.datetime(year,4,1)
            daydeltas = self.ts.index - date
            mindelta = np.amin(np.abs(daydeltas))
            sr_nearest = self.ts[np.abs(daydeltas) == mindelta]

            maxdelta = pd.to_timedelta(f'{maxlag} days')
            if (mindelta <= maxdelta):
                srvg1[year] = round(sr_nearest.iloc[0],2)

        return srvg1


    def xg3(self):
        """Return table of mean highest (GHG) and lowest (GLG) 
        groundwater level for each hydrological year"""

        hydroyears = aq.hydroyear(self.ts1428)
        tbl = pd.DataFrame(index=set(hydroyears))

        for year in tbl.index:
            ts = self.ts1428[hydroyears==year]
            ts = ts[ts.notnull()]
            n1428 = len(ts)

            hg3 = np.nan
            lg3 = np.nan

            if n1428 >= self.n14:

                if self.ref=='datum':
                    hg3 = ts.nlargest(n=3).mean()
                    lg3 = ts.nsmallest(n=3).mean()

                else:
                    hg3 = ts.nsmallest(n=3).mean()
                    lg3 = ts.nlargest(n=3).mean()

            hg3w = np.nan
            lg3s = np.nan

            if n1428 >= self.n14:

                ts_win = ts[aq.season(ts)=='winter']
                ts_sum = ts[aq.season(ts)=='summer']

                if self.ref=='datum':
                    hg3w = ts_win.nlargest(n=3).mean()
                    lg3s = ts_sum.nsmallest(n=3).mean()

                else:
                    hg3w = ts_win.nsmallest(n=3).mean()
                    lg3s = ts_sum.nlargest(n=3).mean()

            tbl.loc[year,'hg3'] = round(hg3,2)
            tbl.loc[year,'lg3'] = round(lg3,2)
            tbl.loc[year,'hg3w'] = round(hg3w,2)
            tbl.loc[year,'lg3s'] = round(lg3s,2)
            tbl.loc[year,'n1428'] = n1428

        return tbl


    def xg3table(self):
        """Return dataframe with spring level (VG), mean highest level
        (LG3) and mean lowest level (LG3) for each year"""

        tbl = self.xg3()
        tbl['vg3'] = self.vg3()
        tbl['vg1'] = self.vg1()

        return tbl


    def gxgtable(self):
        """Return table with GxG for one groundwater series"""

        gxg = pd.DataFrame(index=[self.srname])
        xg3 = self.xg3table()

        for col in xg3.columns:
            sr = xg3[col][xg3[col].notnull()]
            gxg[col] = round(sr.mean(),2)

        for col in xg3.columns:
            sr = xg3[col][xg3[col].notnull()]
            gxg[f'nyr_{col}'] = round(sr.count(),2)

        return gxg

# acer palmatum