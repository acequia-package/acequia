
import warnings
import numpy as np
from pandas import Series, DataFrame
#from pandas.api.types import is_int64_dtype
import pandas as pd


def hydroyear(sr):
    """Return hydrological year for each date in timeseries.
    
    Parameters
    ----------
    sr : pandas Series
        Time series with datetime index.

    Returns
    -------
    pandas Series
        Series with hydrological year for each datetime.

    Notes
    -----
    Hydrological years start on april 1 and end on march 30.
        
    """
    return np.where(sr.index.month<4, sr.index.year-1, sr.index.year)


def season(sr):
    """Return season for each date in timeseries"""
    cond1 = sr.index.month>3
    cond2 = sr.index.month<10
    return np.where(cond1&cond2,"summer","winter")


def get_empty_ts1428(minyear=None, maxyear=None, days=[14,28]):
    """ Return timeseries with dates only on days of the month given by 
    parameter days and only nan values.

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
    pd.Series

    """
    strdates = [str(year)+"-"+str(month)+"-"+str(day) #+' 12:00' 
        for year in list(range(minyear,maxyear+1)) 
        for month in list(range(1,13)) 
        for day in days]
    datetimeindex = pd.DatetimeIndex([pd.Timestamp(x) for x in strdates])
    return Series(index=datetimeindex, name='ts1428', dtype='float')


def get_nearest_date(ts, ts2):
    """Return timeseries ts with nearest date from ts2 and maxlag as 
    possible replacements for missing values.

    Parameters
    ----------
    ts : Series
        Timeseries with measured heads.
    ts2 : Series
        Timeseries with measured heads.

    Returns
    -------
    DataFrame
        Values from ts with nearest date and value from ts2 and 
        difference in days.
            
    """

    # get nearest date for all dates in ts1428
    def get_nearest_date(ts2_date, ts):
        absdelta = abs(ts.index - ts2_date)
        idx = absdelta.get_loc(min(absdelta))
        return ts.index[idx]
    nearest = ts2.index.to_series().apply(get_nearest_date, ts=ts)
    nearest = nearest.to_frame(name='nearest_date')

    nearest['nearest_value'] = ts.loc[nearest['nearest_date']].values
    nearest['time_difference'] = abs(nearest['nearest_date']-nearest.index)
    return nearest


def get_ts1428(ts, maxlag=0, days=[14,28], remove_outer_nans=True):
    """ Return timeseries of measurements on 14th and 28th of each 
    month

    Parameters
    ----------
    ts : pd.Series
        Timeseries with head values.
    maxlag : integer, default 0
        Maximum number of days a measurement is allowed to deviate
        from the 14th or 28th.
    days : list, default [14,28]
        Days of the month in the returned time series.
    remove_leading_nans : boolean, default True
        Remove dates with nans before date with first valid value and 
        after last date with valid value.

    Returns
    -------
    ts : pandas time Series

    Notes
    -----
    When maxlag=0 only measurements taken on the 14th and 28th are 
    selected. When maxlag is 1 or higher, missing values on the 
    14th and 28th are filled in with values from the nearest date,
    with a maximum lag of pllus or minus maxlag days.

    """
    if ts.empty:
        #warnings.warn((f'Groundwater heads series {ts.name} is empty.'))
        return ts

    # resample input series to daymeans
    ts = ts.resample('D').mean().dropna()

    # resample input series to 1428_index
    minyear = ts.index.min().year
    maxyear = ts.index.max().year
    index_1428 = get_empty_ts1428(minyear=minyear, maxyear=maxyear, 
        days=days).index
    ts1428 = ts.reindex(index_1428)

    # fill missing values with value from nearest date, with
    # maxlag as maximum distancew in days
    if (maxlag!=0) & (not ts1428.empty):

        # get table of nearest dates for all dates in ts1428.
        nearest = get_nearest_date(ts, ts1428)

        # select replacement values based on maxlag
        mask = nearest['time_difference']<=pd.Timedelta(maxlag, 'd')
        fill_values = nearest[mask]['nearest_value']

        # replace missing values
        ts1428 = ts1428.fillna(fill_values)

    if remove_outer_nans==True:
        ts1428 = ts1428[ts1428.first_valid_index():ts1428.last_valid_index()]

    return ts1428


def yearseries(ts, dtype='float64'):
    """Return empty time series with years as index, given a list like
    input with dates. All years between min(ts).year and max(ts).year 
    are in the in index (no missing years).
    
    Parameters
    ----------
    ts : pandas Series | list | set | numpy array
        List-like object with dates.
    dtype : dtype, default 'float64'.
        Dtype of series to return.
    
    Returns
    -------
    pandas Series
        
    """

    if isinstance(ts, pd.Series):
        minyear = min(set(ts.index.year))
        maxyear = max(set(ts.index.year))
    elif isinstance(ts, (list, set, np.ndarray)):
        minyear = min(set(ts))
        maxyear = max(set(ts))
    else:
        raise(f'{ts} must be list-like')

    years = range(minyear, maxyear+1)
    ts = Series(index=years, dtype=dtype, name='year')

    return ts


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


def maxfrq(ts):
    """Return maximum of estimated yearly measurement frequencies in
    a time series.

    Input can be pd.Series with pd.DatetimeIndex or pd.Int64Index or
    a list or numpy array with measurement frequencies.
        
    """

    frqs = ['daily','14days','month','seldom','never']

    if isinstance(ts,pd.Series):

        if isinstance(ts.index,pd.DatetimeIndex):
            ts = measfrq(ts)

        if ts.index.dtype==np.int64:

            if pd.to_numeric(ts, errors='coerce').notnull().all():
                ts = ts.apply(measfrqclass).values

            for freq in frqs:
                if np.any(ts==freq): 
                    return freq


    if isinstance(ts,np.ndarray) or isinstance(ts,list):

        if all(pd.notnull(pd.to_numeric(ts,errors='coerce'))):
            ts = [measfrqclass(x) for x in ts]

        for freq in frqs:
            if any([x==freq for x in ts]):
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


