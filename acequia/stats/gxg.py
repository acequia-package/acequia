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


def stats_gxg(ts,ref='datum'):
    """Return table with GxG statistics

    Parameters
    ----------
    ts : aq.GwSeries, pd.Series
        Groundwater head time series

    ref : {'datum','surface'}, optional
        Reference level for groundwater heads


    Return
    ------
    pd.DataFrame"""

    gxg = aq.Gxg(ts, ref=ref)
    return gxg.gxg()


class Gxg:
    """Calculate descriptive statistics for series of measured heads

    Notes
    -----
    Traditionally in the Netherlands groundwater head series are decribed
    using decriptive statistics that characterise the mean highest level
    (GHG), the mean lowest level (GLG) and the mean spring level (GVG).
    These statistics are defined on head series with measurements on the
    14th and 28th of each month. Therefore, heads series are internally
    resampled before calculating statistics.

    For further reference: 
    P. van der SLuijs and J.J. de Gruijter (1985). 'Water table classes: 
    a method to decribe seasonal fluctuation and duration of water table 
    classes on Dutch soil maps.' Agricultural Water Management 10 (1985) 
    109 - 125. Elsevier Science Publishers, Amsterdam.

    """

    n14 = 18

    def __init__(self, gw, srname=None, ref='datum'):
        """Create GxG object

        Parameters
        ----------
        gw : aq.GwSeries, pd.Series
            timeseries with groundwater head measurements

        ref : ['datum','surface'], default 'datum'
            reference level for measurements

        """

        self.gw = gw
        self.srname = srname
        self.ref = ref
        self.surface = None

        if isinstance(self.gw,aq.GwSeries):
            self.srname = gw.name()
            self.ts = gw.heads(ref=ref)
            self.surface = gw.surface()
            ##_tubeprops['surfacelevel'].iat[-1]

        if isinstance(self.gw,pd.Series):
            self.ts = self.gw
            self.srname = self.ts.name

        if self.srname is None:
            self.srname = 'unknown'

        self.ts1428 = aq.ts1428(self.ts,maxlag=3,remove_nans=False)


    def vg3(self):
        """Return VG3 (Spring Level) for each year

        VG3 is calculated as the mean of groundwater head 
        levels on 14 march, 28 march and 14 april

        Return
        ------
        pd.Series"""

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

        return pd.Series(data=vg3,index=years)


    def vg1(self,maxlag=7):
        """Return VG (Spring Level) for each year

        VG1 is calculated as measurement nearest
        to 1 april

        Return
        ------
        pd.Series"""

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


    def xg(self):
        """Return table of GxG groundwater statistics for each 
        hydrological year

        Return
        ------
        pd.DataFrame"""

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
            tbl['vg3'] = self.vg3()
            tbl['vg1'] = self.vg1()
            tbl.loc[year,'n1428'] = n1428

        return tbl


    def gxg(self):
        """Return table with GxG for one head series

        Return
        ------
        pd.DataFrame"""

        gxg = pd.DataFrame(index=[self.srname])
        xg = self.xg()

        for col in xg.columns:
            sr = xg[col][xg[col].notnull()]
            gxg[col] = round(sr.mean(),2)

        for col in xg.columns:
            sr = xg[col][xg[col].notnull()]
            gxg[f'{col}nyr'] = round(sr.count(),2)

        gxg['gt'] = self.gt()

        return gxg


    def gt(self):
        """Return groundwater class table

        Return
        ------
        str"""

        ghg = self.xg()['hg3'].mean()
        glg = self.xg()['lg3'].mean()

        if self.ref=='datum':
            ghg = self.surface-ghg
            glg = self.surface-glg            

        if (ghg<0.20) & (glg<0.50):
            return 'I'

        if (ghg<0.25) & (0.50<glg<0.80):
            return 'II'

        if (0.25<ghg<0.40) & (0.50<glg<0.80):
            return 'II*'

        if (ghg<0.25) & (0.80<glg<0.120):
            return 'III'

        if (0.25<ghg<0.40) & (0.80<glg<0.120):
            return 'III*'

        if (ghg>0.40) & (0.80<glg<0.120):
            return 'IV'

        if (ghg<0.25) & (glg>0.120):
            return 'V'

        if (0.25<ghg<0.40) & (glg>0.120):
            return 'V*'

        if (0.40<ghg<0.80) & (glg>0.120):
            return 'VI'

        if (0.80<ghg<1.40):
            return 'VII'

        if (ghg>1.40):
            return 'VII*'

        return None
        # acer palmatum
