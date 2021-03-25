""" This module contains a class GwGxg that calculates some
descriptive statistics from a series of groundwater head measurements
used by groundwater practitioners in the Netherlands 

History: Created 16-08-2015, last updated 12-02-1016
         Migrated to acequia on 15-06-2019

@author: Thomas de Meij

"""


from datetime import datetime
import datetime as dt
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

##from ..gwseries import GwSeries
import acequia as aq


def stats_gxg(ts,ref='datum'):
    """Return table with GxG statistics

    Parameters
    ----------
    ts : aq.GwSeries, pd.Series
        Groundwater head time series

    ref : {'datum','surface'}, optional
        Reference level for groundwater heads

    Returns
    -------
    pd.DataFrame

    """

    gxg = aq.GxgStats(ts, ref=ref)
    return gxg.gxg()


class GxgStats:
    """Calculate descriptive statistics for time series of measured heads

    Parameters
    ----------
    gw : aq.GwSeries, pd.Series
        timeseries of groundwater head measurements

    ref : ['datum','surface'], default 'datum'
        reference level for measured heads

    srname : str, optional
        name of groundwater head series

    surflevel : float, optional
        surface level height (if ref='datum' this option is ignored)

    Notes
    -----
    In the Netherlands, traditionally groundwater head series are 
    summarized using decriptive statistics that characterise the mean 
    highest level (GHG), the mean lowest level (GLG) and the mean spring 
    level (GVG). These three measures together are reffered to as the GxG.
    The definitions of GHG, GLG and GVG are based on time series with 
    measured heads on the 14th and 28th of each month. Therefore the time 
    series of measrued heads is internally resampled to values on the 14th
    and 28yh before calculating the GxG statistics.

    For further reference: 
    P. van der SLuijs and J.J. de Gruijter (1985). 'Water table classes: 
    a method to decribe seasonal fluctuation and duration of water table 
    classes on Dutch soil maps.' Agricultural Water Management 10 (1985) 
    109 - 125. Elsevier Science Publishers, Amsterdam.

    """

    N14 = 18
    REFERENCE = ['datum','surface']
    FORMS = ['VDS82','VDS89pol','VDS89sto','RUNHAAR']

    def __init__(self, gw, ref=None, srname=None, surflevel=None):
        """Return GxG object"""

        if ref is None:
            ref = self.REFERENCE[0]
  
        if ref not in self.REFERENCE:
            warnings.warn(f'Reference level {ref} is not valid.',
                f'Reference level {self.REFERENCE[0]} is assumed.')
            ref = self.REFERENCE[0]

        self._ref = ref

        if isinstance(gw,aq.GwSeries):

            self._ts = gw.heads(ref=self._ref)
            self.srname = gw.name()
            if surflevel is None:
                self._surflevel = gw.surface()
            else:
                self._surflevel = surflevel
            self._gw = gw

        elif isinstance(gw,pd.Series):

            self._ts = gw
            self.srname = self._ts.name
            self._surflevel = surflevel
            self._gw = None

        else:
            raise(f'{gw} is not of type aq.GwSeries or pd.Series')

        self._ts1428 = aq.ts1428(self._ts,maxlag=3,remove_nans=False)


    def _yearseries(self,ts,dtype='float64'):
        """Return empty time series with years as index with all years
        between min(year) and max(year) in index (no missing years)"""

        if isinstance(ts,pd.Series):
            years = set(ts.index.year)

        elif isinstance(ts,(list,set,np.ndarray)):
            years = set(ts)

        else:
            raise(f'{ts} must be list-like')

        minyear = min(years)
        maxyear= max(years)
        sr = Series(index=range(minyear,maxyear+1),dtype=dtype)
        return sr


    def vg3(self):
        """Return VG3 (Spring Level) for each year

        VG3 is calculated as the mean of groundwater head 
        levels on 14 march, 28 march and 14 april

        Return
        ------
        pd.Series"""

        if hasattr(self,'_vg3'):
            return self._vg3

        self._vg3 = self._yearseries(self._ts1428)
        for i,year in enumerate(self._vg3.index):

            v1 = self._ts1428[dt.datetime(year,3,14)]
            v2 = self._ts1428[dt.datetime(year,3,28)]
            v3 = self._ts1428[dt.datetime(year,4,14)]

            with warnings.catch_warnings():
                # numpy raises a silly warning with nanmean on NaNs
                warnings.filterwarnings(action='ignore', 
                    message='Mean of empty slice')
                self._vg3[year] = round(np.nanmean([v1,v2,v3]),2)

        self._vg3.name = 'VG3'
        return self._vg3


    def vg1(self,maxlag=7):
        """Return VG (Spring Level) for each year

        VG1 is calculated as the single measurement nearest to april 1st

        Return
        ------
        pd.Series """

        if hasattr(self,'_vg1'):
            return self._vg1

        self._vg1 = self._yearseries(self._ts1428)
        for i,year in enumerate(self._vg1.index):

            date = dt.datetime(year,4,1)
            daydeltas = self._ts.index - date
            mindelta = np.amin(np.abs(daydeltas))
            sr_nearest = self._ts[np.abs(daydeltas) == mindelta]

            maxdelta = pd.to_timedelta(f'{maxlag} days')
            if (mindelta <= maxdelta):
                self._vg1[year] = round(sr_nearest.iloc[0],2)

        self._vg1.name = 'VG1'
        return self._vg1


    def xg(self):
        """Return table of GxG groundwater statistics for each 
        hydrological year

        Return
        ------
        pd.DataFrame"""

        if hasattr(self,'_xg'):
            return self._xg

        hydroyears = aq.hydroyear(self._ts1428)
        sr = self._yearseries(hydroyears)
        self._xg = pd.DataFrame(index=sr.index)
        ##self._xg = pd.DataFrame(index=set(hydroyears))

        for year in self._xg.index:

            ts = self._ts1428[hydroyears==year]
            ts = ts[ts.notnull()]
            n1428 = len(ts)

            hg3 = np.nan
            lg3 = np.nan

            if n1428 >= self.N14:

                if self._ref=='datum':
                    hg3 = ts.nlargest(n=3).mean()
                    lg3 = ts.nsmallest(n=3).mean()

                else:

                    hg3 = ts.nsmallest(n=3).mean()
                    lg3 = ts.nlargest(n=3).mean()

            hg3w = np.nan
            lg3s = np.nan

            if n1428 >= self.N14:

                ts_win = ts[aq.season(ts)=='winter']
                ts_sum = ts[aq.season(ts)=='summer']

                if self._ref=='datum':
                    hg3w = ts_win.nlargest(n=3).mean()
                    lg3s = ts_sum.nsmallest(n=3).mean()

                else:
                    hg3w = ts_win.nsmallest(n=3).mean()
                    lg3s = ts_sum.nlargest(n=3).mean()

            self._xg.loc[year,'hg3'] = round(hg3,2)
            self._xg.loc[year,'lg3'] = round(lg3,2)
            self._xg.loc[year,'hg3w'] = round(hg3w,2)
            self._xg.loc[year,'lg3s'] = round(lg3s,2)
            self._xg['vg3'] = self.vg3()
            self._xg['vg1'] = self.vg1()

            self._xg.loc[year,'n1428'] = n1428

        return self._xg


    def gxg(self):
        """Return table with GxG for one head series

        Return
        ------
        pd.DataFrame"""

        if hasattr(self,'_gxg'):
            return self._gxg

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        gxg = pd.Series(name=self.srname) #dtype='float64',

        # xg to gxg
        for col in self._xg.columns:
            sr = self._xg[col][self._xg[col].notnull()]

            if self._ref=='datum':
                gxg[col] = round(sr.mean(),2)

            if self._ref=='surface':
                gxg[col] = round(sr.mean()*100)

                if col=='n1428':
                    gxg[col] = round(sr.mean())

        # gt
        if self._ref=='surface':
            gxg['gt'] = self.gt()

            for form in self.FORMS:
                rowname = 'gvg_'+form.lower()
                gxg[rowname] = self.gvg_approx(form)

        # reference
        gxg['ref'] = self._ref

        # std
        for col in self._xg.columns:

            if col=='n1428':
                continue

            ##sr = self._xg[col][self._xg[col].notnull()]

            if self._ref=='datum':
                gxg[col+'_std'] = np.round(self._xg[col].std(skipna=True),2)

            if self._ref=='surface':
                sr = self._xg[col]*100
                gxg[col+'_std'] = np.round(sr.std(skipna=True))

        # standard error
        for col in self._xg.columns:

            if col=='n1428':
                continue

            if self._ref=='datum':
                sr = self._xg[col]
                gxg[col+'_se'] = np.round(sr.std(skipna=True
                    )/np.sqrt(sr.count()),2)

            if self._ref=='surface':
                sr = self._xg[col]*100
                gxg[col+'_se'] = np.round(sr.std(skipna=True
                    )/np.sqrt(sr.count()),0)

        # count nyears
        for col in self._xg.columns:
            sr = self._xg[col][self._xg[col].notnull()]
            gxg[f'{col}_nyrs'] = np.round(sr.count())

        coldict = {'hg3':'ghg','lg3':'glg','hg3w':'ghgw','lg3s':'glgs',
            'vg3':'gvg3','vg1':'gvg1','n1428':'n1428','hg3nyr':'ghgnyr',
            'lg3nyr':'glgnyr','hg3wnyr':'ghgwnyr','lg3snyr':'glgsnyr',
            'vg3nyr':'gvg3nyr','vg1nyr':'gvg1nyr','n1428nyr':'n1428nyr',
            'gt':'gt','gtref':'gtref'}
        ##self._gxg = self._gxg.rename(columns=coldict)

        self._gxg = gxg.rename(coldict)

        return self._gxg


    def ghg(self):
        """Return mean highest level (GHG)"""

        if not hasattr(self,'_gxg'):
            self._gxg = self.gxg()

        return self._gxg['ghg']


    def glg(self):
        """Return mean highest level (GHG)"""

        if not hasattr(self,'_gxg'):
            self._gxg = self.gxg()

        return self._gxg['glg']


    def gt(self):
        """Return groundwater class table as str"""

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        # do not call self._gxg to avoid recursion error because gt() 
        # is used in gxg()
        ghg = np.nanmean(self._xg['hg3'])*100
        glg = np.nanmean(self._xg['lg3'])*100

        if self._ref=='datum':
            ghg = self._surflevel-ghg
            glg = self._surflevel-glg            

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


    def gvg_approx(self,formula=None):
        """Return GVG calculated with approximation based on GHG and GLG

        Parameters
        ----------
        formula : {'VDS82','VDS89pol','VDS89sto','RUNHAAR'}, default 'VDS82'

        Notes
        -----
        Values for GHG and GLG can be estimated from visual soil profile
        characteristics, allowing mapping of groundwater classes on soil
        maps. GVG unfortunately can not be estimeted is this way.
        Therefore, several regression formulas have been given in litera-
        ture for estimating GVG from GHG and GLG estimates. Three of them
        are implemented: Van der Sluijs (1982), Van der Sluijs (1989) and
        Runhaar (1989)"""


        if formula is None:
            formula = 'VDS82'

        if formula not in self.FORMS:
            warnings.warn(f'Parameter formula has value {formula}, must',
                f'be in {self.FORMS}.')

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        if formula in ['VDS82','RUNHAAR']:
            GHG = np.nanmean(self._xg['hg3'])*100 # must be in cm
            GLG = np.nanmean(self._xg['lg3'])*100

        if formula in ['VDS89pol','VDS89sto']:
            GHG = np.nanmean(self._xg['hg3w'])*100 # must be in cm
            GLG = np.nanmean(self._xg['lg3s'])*100 # ...

        if self._ref=='datum':
            GHG = self._surflevel*100-GHG
            GLG = self._surflevel*100-GLG

        if formula=='VDS82': 
            GVG = np.round(5.4 + 1.02*GHG + 0.19*(GLG-GHG))

        if formula=='RUNHAAR':
            GVG = np.round(0.5 + 0.85*GHG + 0.20*GLG) # (+/-7,5cm)

        if formula=='VDS89pol':
            GVG = np.round(12.0 + 0.96*GHG + 0.17*(GLG-GHG))

        if formula=='VDS89sto':
            GVG = np.round(4.0 + 0.97*GHG + 0.15*(GLG-GHG))

        return GVG

