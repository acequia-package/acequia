

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

    drday = dro.daydrought()

    drsum = dro.summersum()

    drcum = dro.summercum()

    """

    YEARSTART = 'YEAR-01-01'
    YEAREND = 'YEAR-12-31'
    SUMMERSTART = 'YEAR-04-01'
    SUMMEREND = 'YEAR-09-30'
    SUMMERDAYS = 183


    def __init__(self,prc=None,evp=None,stn=None):

        self._prc = prc
        self._evp = evp
        self._rch = self.recharge()
        self._rchsmr = self.summer_recharge()

        if stn is None:
            stn = 'unknown'
        self._stn = stn


    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self._rchsmr)})')


    def recharge(self):
        """Return time series of recharge for all available days

        Calculated as difference between precipitation and evaporation.
        Leading and trailing NaN values are removed."""

        self._rch = self._prc - self._evp

        # remove leading and trailing NaNs
        first = self._rch.first_valid_index()
        last = self._rch.sort_index(ascending=False).first_valid_index()
        self._rch = self._rch[first:last]

        # remove first year if first date is after april 1st
        if not self._rch.index[0].month<4:
            firstyear = self._rch.index[0].year+1
            firstdate = pd.to_datetime(
                self.YEARSTART.replace('YEAR',str(firstyear)))
            self._rch = self._rch[firstdate:]

        # remove last year is last date is before september 30th
        if not self._rch.index[-1].month>9:
            lastyear = self._rch.index[-1].year-1
            lastdate = pd.to_datetime(
                self.YEAREND.replace('YEAR',str(lastyear)))
            self._rch = self._rch[:lastdate]

        return self._rch


    def summer_recharge(self):
        """Return table with array of daily recharges for each summer"""

        # empty table
        years = list(set(self._rch.index.year))
        days = np.arange(0,183)
        self._rchsmr = Series(index=years,dtype=object)
        self._rchsmr.index.name = 'year'

        # daily rechsrge for all years
        for year,rch in self._rch.groupby(by=self._rch.index.year):

            firstdate = self.SUMMERSTART.replace('YEAR',str(year))
            lastdate = self.SUMMEREND.replace('YEAR',str(year))
            rchsmr = self._rch[firstdate:lastdate].values

            self._rchsmr[year] = rchsmr

        return self._rchsmr


    def _cumulative_drought(self,rchsmr):
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

                if np.isnan(daydr[i]):
                    cumdr[i] = daydr[i]

                elif daydr[i] > 0:
                    cumdr[i] = daydr[i]

                else:
                    cumdr[i] = 0

            else:
                cumdr[i] = cumdr[i-1] + daydr[i]
                if cumdr[i]<0:
                    cumdr[i]=0

        return cumdr


    def daydrought(self):
        """Return cumulative drought on daily basis for all years

        Returns
        -------
        pd.DataFrame

        Notes
        -----
        Cumulative meteorological drought is calculated between april 1st
        and september 30th.

        """

        years = list(set(self._rch.index.year))
        days = np.arange(1,self.SUMMERDAYS+1)
        self._daydrought = DataFrame(columns=years,index=days)
        self._daydrought.index.name = 'daynr'
        for year,rch in self._rchsmr.iteritems():
            self._daydrought[year] = self._cumulative_drought(rch)

        return self._daydrought


    def summercum(self):
        """Return maximum cumulative drought for each year"""
        return self.daydrought().max(axis=0)


    def summersum(self):
        """Return sum of drought for all years"""

        self._summersum = Series(index=self._rchsmr.index,dtype=float)

        for year,rch in self._rchsmr.iteritems():
            self._summersum[year] = np.sum(-1*rch)

        return self._summersum

