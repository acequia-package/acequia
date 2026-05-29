""" This module contains a class GwGxg that calculates some
descriptive statistics from a series of groundwater head measurements
used by groundwater practitioners in the Netherlands 

History: Created 16-08-2015, last updated 12-02-1016
         Migrated to acequia on 15-06-2019

@author: Thomas de Meij

"""

import math as _math
import warnings as _warnings
import datetime as _dt
import warnings as _warnings
import numpy as _np
import pandas as _pd
import scipy.stats as _stats

from .utils import get_ts1428, hydroyear, season, yearseries


def stats_gxg(ts, reference='datum', minimal=False, surface=None, minyear=None, maxyear=None):
    """Return table with GxG statistics

    Parameters
    ----------
    ts : pd.Series
        Groundwater head time series
    reference : {'datum','surface'}, optional
        Reference level for groundwater heads
    minimal : bool, default False
        Return minimal number of gxg statistics.
    surface : float, default None
        Surface level.
    minyear : int, optional
        Calculation of summary statistics is done starting from this
        year.
    maxyear : int, optional
        Calculation of summary statistics is done including this year,
        data from later years will be igrnored in symmary statistics.

    Returns
    -------
    pd.DataFrame

    """
    stats = GxgStats(ts, surface=surface, minyear=minyear, maxyear=minyear)
    return stats.gxg(reference=reference, minimal=minimal)


class GxgStats:
    """Calculate descriptive statistics for time series of measured heads.

    Notes
    -----
    In the Netherlands, groundwater head series are summarized using 
    decriptive statistics that characterise the mean 
    highest level (GHG), the mean lowest level (GLG) and the mean spring 
    level (GVG). These three measures together are referred to as the GxG.
    The definitions of GHG, GLG and GVG are based on time series with 
    measured heads on the 14th and 28th of each month. Therefore, the time 
    series of measured heads is internally resampled to values on the 14th
    and 28yh before calculating the GxG statistics.


    References
    ----------    
    Van der Sluijs, P. and J.J. de Gruijter (1985). 'Water table classes: 
    a method to decribe seasonal fluctuation and duration of water table 
    classes on Dutch soil maps.' Agricultural Water Management 10 (1985) 
    109 - 125. Elsevier Science Publishers, Amsterdam.
        
    """

    N14 = 18

    GVG_APPROXIMATIONS = ['SLUIJS82','HEESEN74','SLUIJS76a','SLUIJS76b',
        'SLUIJS89pol','SLUIJS89sto','RUNHAAR89','GAAST06',]

    VGDATES = ['apr1','apr15','mar15']
    VGREFDATE = 'apr1'

    XGSTAS = ['hg3', 'vg3', 'lg3', 'vg_apr1', 'vg1_mar15', 'vg1_apr15', 
        'hg3w', 'lg3s', ]

    GXGSTATS = ['ghg', 'glg', 'ghgw', 'glgs', 'gvg3', 
        'gvg_mar15', 'gvg_apr1', 'gvg_apr15',  'n1428_mean', 'gt', 'gxgref', 
        'ghg_std', 'glg_std', 'ghgw_std', 'glgs_std', 'gvg3_std',
        'gvg_apr1_std', 'gvg_apr15_std', 'gvg_mar15_std', 
        'ghg_nyears', 'glg_nyears', 'ghgw_nyears', 'glgs_nyears', 'gvg3_nyears', 
        'gvg_apr1_nyears', 'gvg_apr15_nyears', 'gvg_mar15_nyears',]

    XG_COLNAMES = ['hg3', 'vg3', 'lg3', 'vg1_mar15', 'vg1_apr1',
        'vg1_apr15', 'hg3w', 'lg3s',]

    TS1428DAYS = ['04-14', '04-28', '05-14', '05-28', 
        '06-14', '06-28', '07-14', '07-28', '08-14', '08-28', '09-14', 
        '09-28', '10-14', '10-28', '11-14', '11-28', '12-14', '12-28', 
        '01-14', '01-28', '02-14', '02-28', '03-14', '03-28']

    GHGDAYS = ['01-14', '01-28', '02-14', '02-28', '03-14', '03-28', '12-28']
    GLGDAYS = ['06-14', '06-28', '07-14', '07-28', '08-14', '08-28', '09-14', 
        '09-28', '10-14']

    GHGDAYS_MINIMAL = ['01-14', '01-28', '02-14', '02-28', '03-14']
    GLGDAYS_MINIMAL = ['08-14', '08-28', '09-14', '09-28']


    def __init__(self, ts=None, surface=None, maxlag=0, minyear=None, maxyear=None):
        """
        ts : pd.Series
            Timeseries of groundwater head measurements (reference is datum level).

        surface : float, optional
            Surface level height (if ref='datum' this option is ignored)

        maxlag : int, default 0
            Maximum number of days the nearest measurement that is used 
            to fill missing values on the 14th of 28th is allowed to 
            be taken before or after the real date.
            
        minyear : int, optional
            Calculation of summary statistics is done starting from this
            year.

        maxyear : int, optional
            Calculation of summary statistics is done including this year,
            data from later years will be igrnored in symmary statistics.

        """
        # set ts
        if ts is None:
            ts = _pd.Series()

        if not isinstance(ts, _pd.Series):
            raise ValueError ((f'{ts} must be pandas Series. Type '
                f'{ts.__class__.__name__} is not supported.'))

        self._tsoriginal = ts
        if not ts.empty:
            self._ts = ts.resample('D').mean().dropna()
        else:
            self._ts = ts
        self._ts1428 = get_ts1428(self._ts, maxlag=maxlag, remove_outer_nans=False)

        self.minyear = minyear
        self.maxyear = maxyear

        # set surface
        if surface is not None:
            self._surface = surface
        else:
            self._surface = _np.nan


    def __repr__(self):
        if not self._ts.name is None:
            return f'{self.__class__.__name__}({self._ts.name}, n={len(self)})'
        return f'{self.__class__.__name__} (n={len(self)})'


    def __len__(self):
        return len(self._ts)


    @staticmethod
    def is_ts1428hydroyear(ts):
        """Return True if input series is a timeseries with measurements 
        on the 14th and 28th of each month for one hydrological year."""

        has_24days = len(ts.index)==24
        has_2years = len(ts.index.year.unique())==2

        tsdays = [f'{str(x.month).zfill(2)}-{str(x.day)}' for x in ts.index]
        has_all_ts1428days = all([x in GxgStats.TS1428DAYS for x in tsdays])
    
        if (has_24days & has_2years & has_all_ts1428days):
            return True
        return False


    @staticmethod
    def is_valid_ts1428hydroyear(ts, validation=None, purpose=None):
        """Return True for hydroyear with enough measurements to estimated
        GHG and GLG.
        
        Parameters
        ----------
        ts : Series
            Timeseries with 24 measurements on the 14th and 28th of each 
            month for one hydrologicval year (april 1st until march 30th).
        
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of series.

        purpose : {'GHG', 'GLG'}, default 'GHG'
            Statistic that will be calculated with the series.

        Returns
        -------
        bool

        Notes
        -----
        strict :
            All measurements on the 24 dates at the 14th and 28th of 
            each month must be present.
        moderate :
            Measurements must be present at all datas with a possibility 
            of contributing to the GxG of at least 5% must be present
            (percentage based on assesment for a large number of series).
        generous :
            Measurements in the periode january 1sth until march 14th must
            be present for GHG and measurements in august and september 
            must be present for GLG.
        maive :
            At least one measurement must be present for each month, 
            regardless of the purpose of the calculation.
            
        """
        if not GxgStats.is_ts1428hydroyear(ts):
            """
            _warnings.warn((f'Input series {ts.name} is not a timeseries '
                f'with measurements on the 14th and 28th of each month for '
                f'one hydrolocial year (april 1st until march 30).'))
            """
            return False


        def has_no_missing_values(ts):
            return all(ts.notnull())


        def has_all_ghg_days(ts):
            return all([x in ts.dropna().index.strftime('%m-%d') 
                for x in GxgStats.GHGDAYS])


        def has_all_glg_days(ts):
            return all([x in ts.dropna().index.strftime('%m-%d') 
                for x in GxgStats.GLGDAYS])


        def has_ghg_days(ts):
            return all([x in ts.dropna().index.strftime('%m-%d') 
                for x in GxgStats.GHGDAYS_MINIMAL])


        def has_glg_days(ts):
            return all([x in ts.dropna().index.strftime('%m-%d') 
                for x in GxgStats.GLGDAYS_MINIMAL])


        def has_all_months(ts):
            return all([x in ts.dropna().index.month for x in range(1,12)])


        # determine validity
        if validation=='strict':
            return has_no_missing_values(ts)

        elif validation=='moderate':
            if purpose=='GHG':
                return has_all_ghg_days(ts)
            elif purpose=='GLG':
                return has_all_glg_days(ts)
            else:
                raise ValueError(f'Unknown calculation purpose "{purpose}".')

        elif validation=='generous':
            if purpose=='GHG':
                return has_ghg_days(ts)
            elif purpose=='GLG':
                return has_glg_days(ts)
            else:
                raise ValueError(f'Unknown calculation purpose "{purpose}".')

        elif validation=='naive':
            return has_all_months(ts)

        else:
            raise ValueError(f'Unknown validation method "{validation}".')


    @property
    def empty(self):
        if self._ts.empty:
            return True
        return False


    @staticmethod
    def _ts1428hydroyear_hg3_values(ts, validation='moderate'):
        """Return three highest values in a hydrological year for a
        ts1428hydroyear series. """
        if GxgStats.is_valid_ts1428hydroyear(ts, validation=validation, purpose='GHG'):
            hg3 = ts.nlargest(n=3)
            return hg3
        else:
            return _pd.Series(name=ts.name)


    @staticmethod
    def _ts1428hydroyear_lg3_values(ts, validation='moderate'):
        """Return three lowest values in a hydrological year for a
        ts1428hydroyear series. """
        if GxgStats.is_valid_ts1428hydroyear(ts, validation=validation, purpose='GLG'):
            lg3 = ts.nsmallest(n=3)
            return lg3
        else:
            return _pd.Series(name=ts.name)


    @staticmethod
    def _ts1428hydroyear_xg3table(xg3):
        """Return xg3 as table with details about series."""
        seriesname = xg3.name
        xg3 = xg3.to_frame(name='head')
        xg3.insert(0, 'series', seriesname)
        xg3.insert(1, 'date', xg3.index)
        xg3['rank'] = range(1, len(xg3.index)+1)
        xg3['year'] = xg3.index.year
        xg3['monthday'] = xg3.index.strftime('%m-%d')
        return xg3.reset_index(drop=True)


    def hg3_table(self, validation='moderate', period='year'):
        """Return HG3 values for each year with sufficient data.

        Parameters
        ----------
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of time series.
        
        Returns
        -------
        DataFrame
            Table with HG3 for each year and details about series.
            
        """
        hg3_days = []
        for year, ts in self._ts1428.groupby(hydroyear(self._ts1428)):

            if period=='winter':
                # all but summer days is made NaN
                ts.loc[~(season(ts)=='winter')]=_np.nan
            elif period=='summer':
                raise ValueError((f'Parameter "period" can not be "{period}" '
                    f'for calculation HG3. Did you mean period="winter"?'))

            if self.is_valid_ts1428hydroyear(ts, validation=validation, purpose='GHG'):

                hg3 = self._ts1428hydroyear_hg3_values(ts, validation=validation)
                hg3table = self._ts1428hydroyear_xg3table(hg3)
                hg3_days.append(hg3table)

        if hg3_days:
            hg3days = _pd.concat(hg3_days, ignore_index=True)
        else:
            hg3days = _pd.DataFrame()

        return hg3days


    def lg3_table(self, validation='moderate', period='year'):
        """Return LG3 values for each year with sufficient data.

        Parameters
        ----------
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of series.

        period : {'year','summer'}, defaullt 'year
            LG3 is calculated over entire hydrological year ('year')
            or only the summer half year (april-september).
        
        Returns
        -------
        DataFrame
            Table with LG3 for each year and details about series.
            
        """
        lg3_days = []
        for year, ts in self._ts1428.groupby(hydroyear(self._ts1428)):

            if period=='summer':
                # all but summer days is made NaN
                ts.loc[~(season(ts)=='summer')]=_np.nan
            elif period=='winter':
                raise ValueError((f'Parameter "period" can not be "{period}" '
                    f'for calculation of LG3. Did you mean period="summer"?'))

            if self.is_valid_ts1428hydroyear(ts, validation=validation, 
                purpose='GLG'):
                lg3 = self._ts1428hydroyear_lg3_values(ts, 
                    validation=validation)
                lg3table = self._ts1428hydroyear_xg3table(lg3)
                lg3_days.append(lg3table)

        if (validation in ['moderate','strict', 'naive']) & (period=='summer'):
            _warnings.warn((f'Calculation of GLG for period="summer" '
                f'will never yield results because any measurements on '
                f'october 14th are set to NaN while these have to '
                f'be present in validation category "{validation}".'))

        if lg3_days:
            lg3days = _pd.concat(lg3_days, ignore_index=True)
        else:
            lg3days = _pd.DataFrame()
        return lg3days


    def _select_minmaxyear(self, tbl):
        # select years if either self.minyear or self.maxyear is given
        # else return all years
        minyear = tbl.index.min()
        maxyear = tbl.index.max()
        if self.minyear:
            minyear = self.minyear
        if self.maxyear:
            maxyear = self.maxyear
        return tbl.loc[minyear:maxyear].copy()


    def hg3(self, validation='moderate', period='year'):
        """Return HG3 for each hydrological year.

        Parameters
        ----------
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of series.

        Returns
        -------
        Series
            HG3 for each year.
            
        """
        # get hg3 for each year
        hg3 = self.hg3_table(validation=validation, period=period)

        if not hg3.empty:
            hg3 = hg3.groupby('year')['head'].mean()
        else:
            hg3 = _pd.Series(index=_pd.RangeIndex(self._ts1428.index.year.min(), self._ts1428.index.year.max()), dtype='float')
        hg3.name = self._ts.name
        
        # fil in missing years
        hg3 = hg3.reindex(_pd.RangeIndex(self._ts1428.index.year.min(), self._ts1428.index.year.max()))

        # select years if either minyear or maxyear is given
        if (self.minyear is not None) | (self.maxyear is not None):
            hg3 = self._select_minmaxyear(hg3)

        return hg3


    def lg3(self, validation='moderate', period='year'):
        """Return LG3 for each hydrological year.

        Parameters
        ----------
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of time series.

        Returns
        -------
        Series
            LG3 for each year.
            
        """
        # get lg2 fr each year
        lg3 = self.lg3_table(validation=validation, period=period)
        if not lg3.empty:
            lg3 = lg3.groupby('year')['head'].mean()
        else:
            lg3 = _pd.Series(index=_pd.RangeIndex(self._ts1428.index.year.min(), self._ts1428.index.year.max()), dtype='float')
        lg3.name = self._ts.name
        
        # fil in missing years
        lg3 = lg3.reindex(_pd.RangeIndex(self._ts1428.index.year.min(), self._ts1428.index.year.max()))

        # select years if either minyear or maxyear is given
        if (self.minyear is not None) | (self.maxyear is not None):
            lg3 = self._select_minmaxyear(lg3)

        return lg3


    def vg3(self, minN=3):
        """Return VG3 (Spring Level) for each year. VG3 is calculated 
        as the mean of groundwater head levels on 14 march, 28 march 
        and 14 april. If any of these measurements lacks, a NaN value 
        is returned.

        Parameters
        ----------
        minN : {1, 2, 3}, default 3
            Minimal number of measurements to calculate VG3, else return 
            NaN.

        Return
        ------
        pd.Series


        Notes
        -----
        Calculation of GVG based on the average of three dates was 
        introduced by Finke et al. (1999).

        References
        ----------
        Finke, P.A., D.J. Brus, T. Hoogland, J. Oude Voshaar, F. de Vries
        & D. Walvoort (1999). Actuele grondwaterinformatie 1:10.000 in de
        waterschappen Wold en Wieden en Meppelerdiep. Gebruik van digitale 
        maaiveldshoogtes bij de kartering van GHG, GVG en GLG. SC-rapport
        633. (in Dutch).
            
        """
        if self._ts1428.empty:
            return _pd.Series()

        def vg3(ts1428):
            year = min(ts1428.index.year)
            vg3 = _pd.Series(index=[_dt.datetime(year,3,14),
                _dt.datetime(year,3,28), _dt.datetime(year,4,14)])
            try:
                vg3.iloc[0] = ts1428[vg3.index[0]]
                vg3.iloc[1] = ts1428[vg3.index[1]]
                vg3.iloc[2] = ts1428[vg3.index[2]]
                if len(vg3.isnull())>=minN:
                    return vg3.mean(skipna=True)
            except KeyError:
                return _np.nan
            return _np.nan

        # get series of vg3 for each year
        vg3 = self._ts1428.groupby(self._ts1428.index.year).apply(vg3)

        # select years if either minyear or maxyear is given
        if (self.minyear is not None) | (self.maxyear is not None):
            vg3 = self._select_minmaxyear(vg3)

        return vg3.round(2)


    def vg1(self, refdate=VGREFDATE, maxlag=0):
        """Return estimate of the VG (Spring Level) for each year.

        Parameters
        ----------
        refdate : {'apr1','apr15','mar15'}, default 'apr1'
            reference date for estimating VG

        maxlag : number
            maximum allowed difference between measurement date en refdate

        Return
        ------
        pd.Series 

        Notes
        -----
        Until 1999 the VG (Voorjaarsgrondwaterstand, Spring Level) was
        estimated as the single measurement closest to the reference date.
        The reference date for calculation of the GVG was changed from
        april 15th to april 1st in de early eighties. 
        In 2000 the Cultuurtechnisch Vademecum proposed march 15th as the 
        new reference date for the GVG, but this proposal was not generally 
        adopted. In practice april 1st is allways used as reference date 
        and this is used as default for calculations.
        
        In 1999 a new calculation method was introduced bij Finke et al. 
        (1999) in which the VG was calculated as the average of 
        measurements on march 14th, march 28th and april 14th. This method 
        called the VG3 became the new standard practice and the VG1 was 
        deprecated.

        References
        ----------
        Finke, P.A., D.J. Brus, T. Hoogland, J. Oude Voshaar, F. de Vries
        & D. Walvoort (1999). Actuele grondwaterinformatie 1:10.000 in de
        waterschappen Wold en Wieden en Meppelerdiep. Gebruik van digitale 
        maaiveldshoogtes bij de kartering van GHG, GVG en GLG. SC-rapport
        633. (in Dutch).

        Van der Gaast, J.W.J., H.Th.L. Massop & H.R.J. Vroon (2009). Actuele
        grondwaterstandsituatie in natuurgebieden. Rapport 94 WOT. Alterra,
        Wageningen. (in Dutch).
        
        Van der Sluijs en Van Heesen (1989)
            
        """
        if self._ts1428.empty:
            return _pd.Series()

        if refdate not in self.VGDATES:
            raise ValueError((f'Reference date {refdate} for GVG is not '
                f'recognised. Reference date must be in "{self.VGDATES}".'))

        def get_vg1_for_calenderyear(ts, refdate=None, maxlag=0):

            year = ts.index[0].year
            if refdate=='apr1':
                date = _dt.datetime(year,4,1)
            if refdate=='apr15':
                date = _dt.datetime(year,4,15)
            if refdate=='mar15':
                date = _dt.datetime(year,3,15)

            daydeltas = ts.index-date
            mindelta = _np.amin(_np.abs(daydeltas))
            maxdelta = _pd.to_timedelta(f'{maxlag} days')

            sr_nearest = ts[_np.abs(daydeltas) == mindelta]
            if (mindelta <= maxdelta):
                vg1 = _np.round(sr_nearest.iloc[0],2)
            else:
                vg1 = _np.nan
            return vg1

        vg1 = self._ts1428.groupby(self._ts1428.index.year).apply(
            get_vg1_for_calenderyear, refdate=refdate, maxlag=maxlag
            )
        vg1.name = self._ts.name

        # select years if either minyear or maxyear is given
        if (self.minyear is not None) | (self.maxyear is not None):
            vg1 = self._select_minmaxyear(vg1)

        return vg1


    def _calculate_xg_nap(self, validation=None, maxlag=0, minN=3):
        """Return table with xg statistics for each year in time series.

        Parameters
        ----------
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of time series.

        maxlag : number
            Maximum allowed difference between measurement date en 
            chosen reference date for spring level.

        minN : {1, 2, 3}, default 3
            Minimal number of measurements to calculate VG3, else return 
            NaN.

        Return
        ------
        pd.DataFrame
                    
        """ 

        if self._ts1428.empty:
            xg = _pd.DataFrame(columns=self.XG_COLNAMES)
            return xg

        data = {
            'hg3' : self.hg3(validation=validation, period='year'),
            'lg3':self.lg3(validation=validation, period='year'),
            'vg3':self.vg3(minN=minN),
            'vg1_apr1':self.vg1(refdate='apr1', maxlag=maxlag),
            'vg1_mar15':self.vg1(refdate='mar15', maxlag=maxlag),
            'vg1_apr15':self.vg1(refdate='apr15', maxlag=maxlag),
            'hg3w':self.hg3(validation=validation, period='winter'),
            # generous is the only validation method that produces a result for lg3s
            'lg3s':self.lg3(validation='generous', period='summer'), 
            }
        xg = _pd.concat(data, axis=1)

        return xg


    def xg(self, reference='datum', validation='moderate', maxlag=0, minN=3, name=True):
        """Return table of GxG groundwater statistics for each 
        hydrological year

        Parameters
        ----------
        reference : {'datum','surface'}, default 'datum'
            Reference level for gxg statistics.
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of time series.
        maxlag : number
            Maximum allowed difference between measurement date en 
            chosen reference date for spring level.
        minN : {1,2,3}, default 3
            HG3, LG3 and VG3 for each year are calculated only if at 
            least minN values are available.
        name : bool, default True
            Include series name in index.

        Returns
        -------
        pd.DataFrame

        Notes
        -----
        Results are given in meter for reference level 'datum' and in 
        centimeter for reeference level 'surface'.
            
        """

        if reference not in ['datum','surface']:
            _warnings.warn((f'Unknown reference level "{reference}". '
                f'Reference level "datum" is assumed.'))
            reference = 'datum'

        xg = self._calculate_xg_nap(validation=validation, maxlag=maxlag)

        if reference=='surface':
            for col in xg.columns:
                xg[col] = (self._surface - xg[col]) * 100 # convert unit meter 1 to centimeter 100
                xg[col] = xg[col].apply(lambda x:_math.floor(x) if 
                    not _np.isnan(x) else x)

        # select years if either minyear or maxyear is given
        # xg is a dataframe with a multilevel index (series, year)
        if (self.minyear is not None) |(self.maxyear is not None):
            xg = self._select_minmaxyear(xg)

        if name==True:
            # this creates a multiindex seriesname, year
            # don't do anything after this, to avoid multindex headaches
            xg = _pd.concat({self._ts.name: xg}, names=['series','year'])

        return xg


    def ghg(self, reference='datum', validation='moderate', period='year'):
        """Return mean highest level (GHG)."""

        if self._ts1428.empty:
            return _np.nan

        # get ghg
        ghgref = self.hg3(validation=validation, period=period).mean(skipna=True)
        
        if reference=='surface':
            return _np.floor((self._surface-ghgref)*100)

        return _np.round(ghgref, 2)


    def glg(self, reference='datum', validation='moderate', period='year'):
        """Return mean highest level (GHG)."""

        if self._ts1428.empty:
            return _np.nan

        # get glg
        glgref = self.lg3(validation=validation, period=period).mean(skipna=True)

        if reference=='surface':
            return _np.floor((self._surface-glgref)*100)

        return _np.round(glgref, 2)


    def gvg(self, reference='datum'):
        """Return mean spring level (GVG)"""

        gvgnap = self.vg3().mean(skipna=True)

        if reference=='surface':
            return _np.round((self._surface-gvgnap)*100, 0)

        return _np.round(gvgnap, 2)


    def gt(self, validation='moderate'):
        """Return groundwater class table as str"""

        # calculate ghg and glg in cm relative to surtface level
        ghg = self.ghg(reference='surface', validation=validation, period='year')
        glg = self.glg(reference='surface', validation=validation, period='year')

        if (ghg<20) & (glg<50):
            return 'I'

        if (ghg<25) & (50<glg<80):
            return 'II'

        if (25<ghg<40) & (50<glg<80):
            return 'II*'

        if (ghg<25) & (80<glg<120):
            return 'III'

        if (25<ghg<40) & (80<glg<120):
            return 'III*'

        if (ghg>40) & (80<glg<120):
            return 'IV'

        if (ghg<25) & (glg>120):
            return 'V'

        if (25<ghg<40) & (glg>120):
            return 'V*'

        if (40<ghg<80) & (glg>120):
            return 'VI'

        if (80<ghg<140):
            return 'VII'

        if (ghg>140):
            return 'VII*'

        return _np.nan
        # acer palmatum


    def gvg_approximations(self, reference='surface', validation='moderate'): ##, formula=None):
        """Return GVG in centimeter rellative to surface, calculated with approximation based on GHG and GLG

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
        Runhaar (1989).
                
        """
        # create empty series with right index
        rowlabels = [f'gvg_{x.lower()}' for x in self.GVG_APPROXIMATIONS]
        rowlabels = ['ghg', 'glg', 'gvg'] + rowlabels
        sr = _pd.Series(index=rowlabels, dtype='float')

        if _np.isnan(self._surface):
            _warnings.warn((f'No GVG appromations calculated because '
                f'given surface level for time series {self._ts.name} '
                f'is NaN.'))
            return sr

        ##if not hasattr(self,'_xgnap'):
        ##    self._xgnap = self._calculate_xg_nap()

        # GHG and GLG for hydrological year
        ghgnap = self.ghg(reference='datum', validation=validation, period='year')
        glgnap = self.glg(reference='datum', validation=validation, period='year')
        GHG = (self._surface-ghgnap)*100
        GLG = (self._surface-glgnap)*100

        # GHG and GLG for summer and winter
        ghg_w = self.ghg(reference='datum', validation=validation, period='winter')
        glg_s = self.glg(reference='datum', validation=validation, period='summer')
        GHGw = (self._surface-ghg_w)*100
        GLGs = (self._surface-glg_s)*100

        # gvg from measurements for reference
        gxg = self.gxg(reference='surface')
        sr['ghg'] = self.ghg(reference='surface')
        sr['glg'] = self.glg(reference='surface')
        sr['gvg'] = self.gvg(reference='surface')

        # ghg and glg in centimeter relative to surface level
        sr['gvg_heesen74'] = 0.2*(GLG-GHG)+GHG+12
        sr['gvg_sluijs76a'] = 0.15*(GLG-GHG)+(1.01*GHG)+14.3
        sr['gvg_sluijs76b'] = 1.03*GHG+27.3 # assumes GVG at april 14th
        sr['gvg_sluijs82'] = 5.4 + 1.02*GHG + 0.19*(GLG-GHG)
        sr['gvg_runhaar89'] = 0.5 + 0.85*GHG + 0.20*GLG # (+/-7,5cm)
        sr['gvg_sluijs89pol'] = 12.0 + 0.96*GHGw + 0.17*(GLGs-GHGw)
        sr['gvg_sluijs89sto'] = 4.0 + 0.97*GHGw + 0.15*(GLGs-GHGw)
        sr['gvg_gaast06'] = 13.7 + 0.70*GHG + 0.25*GLG

        if reference=='surface':
            sr = _np.round(sr, 0)

        if reference=='datum':
            sr = _np.round(self._surface-sr/100, 2)

        return sr


    def gxg(self, reference='datum', validation='moderate', maxlag=0, minimal=False):
        """Return table with GxG for one head series

        Parameters
        ----------
        reference : {'datum','surface'}, default 'datum'
            reference level for gxg statistics
        validation : {'strict', 'moderate', 'generous', 'naive'}
            Method to establish validity of time series.
        maxlag : number
            Maximum allowed difference between measurement date en 
            chosen reference date for spring level.
        minimal : bool, default True
            return minimal selection of stats

        Returns
        -------
        DataFrame
            Table with GxG statistics.
            
        """
        # empty dataframe for gxg statistics
        gxg_rowlabels = (['gt'] + [f'{x}_mean' for x in self.XG_COLNAMES] 
            + [f'{x}_ci95' for x in self.XG_COLNAMES]
            + [f'{x}_nyears' for x in self.XG_COLNAMES] 
            + [f'{x}_std' for x in self.XG_COLNAMES]
            + ['surface', 'minyear', 'maxyear']
            )
        gxg = _pd.Series(index=gxg_rowlabels, name=self._ts.name, dtype='object')

        # get dataframe with xg statistics
        xgnap = self.xg(reference='datum', name=False, validation=validation, maxlag=maxlag)

        if xgnap.empty:
            gxg = _pd.Series()
            return gxg

        # get gxg estimates as means from xg columns
        for colname in xgnap.columns:
            gxg[f'{colname}_mean'] = xgnap[colname].mean(skipna=True)

        # calculate 95% confidence interval of the gxg
        for colname in xgnap.columns:
            gxg[f'{colname}_ci95'] = self._confidence_mean(xgnap[colname], alfa=0.05)

        # calculate number of years
        for colname in xgnap.columns:
            gxg[f'{colname}_nyears'] = xgnap[colname].count()

        # calculate std
        for colname in xgnap.columns:
            gxg[f'{colname}_std'] = xgnap[colname].std(skipna=True)

        if reference=='datum':
            # round to 2 decimals
            rowlabels= [x for x in gxg.index.values if x.endswith(('_mean', '_ci95', 'std'))]
            for label in rowlabels:
                gxg[label] = _np.round(gxg[label], 2)

        if reference=='surface':
            # round to centimeters

            rowlabels= [x for x in gxg.index.values if x.endswith('_mean')]
            for label in rowlabels:
                gxg[label] = _np.round((self._surface - gxg[label]) * 100, 0)

            rowlabels= [x for x in gxg.index.values if x.endswith('_ci95')]
            for label in rowlabels:
                gxg[label] = _np.round(gxg[label] * 100, 0)

            rowlabels= [x for x in gxg.index.values if x.endswith('_std')]
            for label in rowlabels:
                gxg[label] = _np.round(gxg[label] * 100, 0)


        # add rows to gxg table
        gxg['gt'] = self.gt()
        gxg['minyear'] = xgnap.index.min()
        gxg['maxyear'] = xgnap.index.max()
        gxg['surface'] = self._surface
        gxg['gxgref'] = reference

        # rename row labels
        for rowname in gxg.index:
            if rowname.endswith('_std'):
                continue
            if rowname.startswith('hg3_'):
                gxg = gxg.rename(
                    index={rowname:f'ghg_{rowname.split("_",1)[1]}'})
            if rowname.startswith('vg3_'):
                gxg = gxg.rename(
                    index={rowname:f'gvg_{rowname.split("_",1)[1]}'})
            if rowname.startswith('lg3_'):
                gxg = gxg.rename(
                    index={rowname:f'glg_{rowname.split("_",1)[1]}'})
            if rowname.startswith('vg1'):
                gxg = gxg.rename(
                    index={rowname:f'gvg_{rowname.split("_",1)[1]}'})
            if rowname.startswith('hg3w_'):
                gxg = gxg.rename(
                    index={rowname:f'ghgw_{rowname.split("_",1)[1]}'})
            if rowname.startswith('lg3s_'):
                gxg = gxg.rename(
                    index={rowname:f'glgs_{rowname.split("_",1)[1]}'})

        for rowname in gxg.index:
            if rowname.endswith('mean'):
                gxg = gxg.rename(
                    index={rowname:f'{rowname.rsplit("_",1)[0]}'})

        if minimal:
            rowlabels = ['gt','ghg', 'gvg', 'glg', #'gvg_apr1', 
                'surface', 'minyear', 'maxyear', 
                'ghg_ci95','gvg_ci95','glg_ci95',
                'ghg_nyears','gvg_nyears', 'glg_nyears',
                'gxgref',
                ]
            gxg = gxg[gxg.index.intersection(rowlabels)]
            gxg = gxg.rename({'ghg':'ghg_cmmv', 'gvg':'gvg_cmmv', 
                'glg':'glg_cmmv', 'gvg_apr1':'gvg_apr1_cmmv'})

        return gxg


    @staticmethod
    def _confidence_mean(sr, alfa=0.05):
        """Return confidence interval of the mean for a series given 
        confidence level alfa."""
        #confi = scipy.stats.t.interval(1-alfa, count-1, loc=mean, scale=sem)
        alfa = 1-0.05/2
        df = sr.count()-1
        t = _stats.t.ppf(alfa, df)
        ci = t * sr.sem(skipna=True, ddof=1)
        return ci

