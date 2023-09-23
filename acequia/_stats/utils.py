
import numpy as np
from pandas import Series, DataFrame
from pandas.api.types import is_int64_dtype
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

    strdates = [str(year)+"-"+str(month)+"-"+str(day) #+' 12:00' 
                for year in list(range(minyear,maxyear+1)) 
                for month in list(range(1,13)) for day in days]

    dates = [pd.Timestamp(x) for x in strdates]

    return pd.DatetimeIndex(dates)


def ts1428(sr,maxlag=0,remove_nans=True, days=[14,28]):
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
    days : list, default [14,28]
        days in DatetimeIndex

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
    idx1428 = index1428(minyear=minyear,maxyear=maxyear,days=days)
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


def measfrqclass(n):
    """Return measurement frequency class given number of yearly 
    measurements n"""

    if n>27: 
        return "daily"
    elif n>12: 
        return "14days"
    elif n>9: 
        return "month"
    elif n>0:
        return "seldom"
    else: 
        return "never"


def measfrq(ts):
    """Return estimated measurement frequency for each year in a time 
    series"""

    yearfrq = ts.groupby(ts.index.year).count()
    yearfrq.index.name = 'year'
    return yearfrq.apply(measfrqclass)


def maxfrq(sr):
    """Return maximum of estimated yearly measurement frequencies in
    a time series.

    Input can be pd.Series with pd.DatetimeIndex or pd.Int64Index or
    a list or numpy array with measurement frequencies"""

    frqs = ['daily','14days','month','seldom','never']

    if isinstance(sr,pd.Series):

        if isinstance(sr.index,pd.DatetimeIndex):
            sr = measfrq(sr)

        #if isinstance(sr.index,pd.Int64Index):
        if is_int64_dtype(sr.index.dtype):

            if pd.to_numeric(sr, errors='coerce').notnull().all():
                sr = sr.apply(measfrqclass).values

            for freq in frqs:
                if np.any(sr==freq): 
                    return freq


    if isinstance(sr,np.ndarray) or isinstance(sr,list):

        if all(pd.notnull(pd.to_numeric(sr,errors='coerce'))):
            sr = [measfrqclass(x) for x in sr]

        for freq in frqs:
            if any([x==freq for x in sr]):
                return freq

    """
        ts = np.array(ts)
        allint = all([x.dtype=='int32' for x in ts])
        allfloat = all([x.dtype=='float64' for x in ts])

        # ts is a np.ndarray or list of numbers
        if allint or allfloat:
            ts = [measfrqclass(x) for x in ts]

    for freq in frqs:
        if np.any(ts==freq): 
            return freq
    """


