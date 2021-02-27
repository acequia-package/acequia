

import warnings
import numpy as np
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
import pandas as pd


class MeteoDrought:
    """Calculate statistical measures of meteorological drought from
    time series

    Parameters
    ----------
    prc : pd.Series
        time series with precipitation data

    evp : pd.Series
        time series with evaporation data

    Examples
    --------

    dro = aq.MeteoDrought(prc,evp)

    drsum = dro.summersum()

    drcum = dro.summercum()

    """

    YEARSTART = 'YEAR-01-01'
    YEAREND = 'YEAR-12-31'
    SUMMERSTART = 'YEAR-04-01'
    SUMMEREND = 'YEAR-09-30'
    SUMMERDAYS = 183


    def __init__(self,prc=None,evp=None):

        self.prc = prc
        self.evp = evp
        self.rch = self.recharge()
        self.rchsmr = self.summer_recharge()


    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self.rchsmr)})')


    def recharge(self):
        """Return time series of recharge for all available days

        Calculated as difference between precipitation and evaporation.
        Leading and trailing NaN values are removed."""

        self.rch = self.prc - self.evp

        # remove leading and trailing NaNs
        first = self.rch.first_valid_index()
        last = self.rch.sort_index(ascending=False).first_valid_index()
        self.rch = self.rch[first:last]

        # remove first year if first date is after april 1st
        if not self.rch.index[0].month<4:
            firstyear = self.rch.index[0].year+1
            firstdate = pd.to_datetime(
                self.YEARSTART.replace('YEAR',str(firstyear)))
            self.rch = self.rch[firstdate:]

        # remove last year is last date is before september 30th
        if not self.rch.index[-1].month>9:
            lastyear = self.rch.index[-1].year-1
            lastdate = pd.to_datetime(
                self.YEAREND.replace('YEAR',str(lastyear)))
            self.rch = self.rch[:lastdate]

        return self.rch


    def summer_recharge(self):
        """Return table with array of daily recharges for each summer"""

        # empty table
        years = list(set(self.rch.index.year))
        days = np.arange(0,183)
        self.rchsmr = Series(index=years,dtype=object)
        self.rchsmr.index.name = 'year'

        # daily rechsrge for all years
        for year,rch in self.rch.groupby(by=self.rch.index.year):

            firstdate = self.SUMMERSTART.replace('YEAR',str(year))
            lastdate = self.SUMMEREND.replace('YEAR',str(year))
            rchsmr = self.rch[firstdate:lastdate].values

            self.rchsmr[year] = rchsmr

        return self.rchsmr


    def cumulative_drought(self,rchsmr):
        """Return daily values of cumulative drought for one summer

        Parameters
        ----------
        rchsmr : np.array
            daily values of recharge between april 1st and september 30th

        Returns
        -------
        numpy.array with daily cumulative drought 

        """

        daydr = -1*rchsmr
        cumdr = np.zeros(len(daydr))

        for i,val in enumerate(daydr):

            if i==0:
                if daydr[i] > 0:
                    cumdr[i] = daydr[i]
                else:
                    cumdr[i] = 0

            else:
                cumdr[i] = cumdr[i-1] + daydr[i]
                if cumdr[i]<0:
                    cumdr[i]=0

        return cumdr


    def daycum(self):
        """Return cumulative drought on daily basis for all years

        Notes
        -----
        Cumulative meteorological drought is calculated between april 1st
        and september 30th.

        """

        years = list(set(self.rch.index.year))
        days = np.arange(0,self.SUMMERDAYS)
        self.cumdr = DataFrame(columns=years,index=days)

        for year,rch in self.rchsmr.iteritems():
            self.cumdr[year] = self.cumulative_drought(rch)

        return self.cumdr


    def summercum(self):
        """Return maximum cumulative drought for each year"""
        return self.daycum().max(axis=0)


    def summersum(self):
        """Return sum of drought for all years"""

        self.smrsum = Series(index=self.rchsmr.index,dtype=float)

        for year,rch in self.rchsmr.iteritems():
            self.smrsum[year] = np.sum(-1*rch)

        return self.smrsum

