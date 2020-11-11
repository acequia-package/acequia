
import numpy as np
from pandas import Series, DataFrame
import pandas as pd


def hydroyear(sr):
    """Return hydrological year for each date in timeseries

    Note
    ----
    A hydrological year strts on april 1st and ends on march 30th 
    """
    return np.where(sr.index.month<4,sr.index.year-1,sr.index.year)


def season(sr):
    """Return season for each date in timeseries"""
    cond1 = sr.index.month>3
    cond2 = sr.index.month<10
    return np.where(cond1&cond2,"summer","winter")


def index1428(minyear=None,maxyear=None,days=[14,28]):
    """ Return datetimeindex with only daynumber in days

    Parameters
    ----------
    minyear : number
        first year in DatetimeIndex
    maxyear : number
        first year in DatetimeIndex
    days : list, default [14,28]
        days in DatetimeIndex

    Returns
    -------
    pd.DatetimeIndex

    """

    strdates = [str(day)+"-"+str(month)+"-"+str(year) #+' 12:00' 
                for year in list(range(minyear,maxyear+1)) 
                for month in list(range(1,13)) for day in days]

    dates = [pd.Timestamp(x) for x in strdates]

    return pd.DatetimeIndex(dates)


def ts1428(sr,maxlag=0,remove_nans=True):
    """ Return timeseries of measurements on 14th and 28th of each 
    month

    Parameters
    ----------
    sr : pd.Series
        timeseries
    maxlag : integer, default 0
        maximum number of days a measurement is allowed to deviate
        from the 14th or 28th
    remove_nans : boolean, default True
        remove values with nans before first valid value

    Returns
    -------
    sr : pandas time Series

    Notes
    -----
    When maxlag=0 only measurements on the 14th and 28th are 
    selected. When maxlag is 1 or higher, missing values on the 
    14th and 28th are filled in with values from the nearest date,
    with a maximum deviation of maxlag days.

    """

    # create empty timeseries with 1428 index
    minyear = sr.index.min().year
    maxyear = sr.index.max().year
    idx1428 = index1428(minyear=minyear,maxyear=maxyear,days=[14,28])
    ts1428 = pd.Series(data=np.nan, index=idx1428)

    # add values to timeseries ts1428
    for date in ts1428.index:

        daydeltas = sr.index - date # type(daydeltas) = TimedeltaIndex
        mindelta = np.amin(np.abs(daydeltas))
        sr_nearest = sr[np.abs(daydeltas) == mindelta]

        maxdelta = pd.to_timedelta(f'{maxlag} days')
        if (mindelta <= maxdelta) & (len(sr_nearest)!=0):
            ts1428[date] = sr_nearest.iloc[0]

    if remove_nans==True:
        ts1428 = ts1428[ts1428.first_valid_index():ts1428.last_valid_index()]

    return ts1428

