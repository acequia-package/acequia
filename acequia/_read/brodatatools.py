

import sys as _sys
import warnings as _warnings
import numpy as _np
#from pandas import Series, DataFrame
import pandas as _pd
#import geopandas as gpd

from brodata.gmw import GroundwaterMonitoringWell
import brodata as _brodata

from .._core.gwseries import GwSeries


def gmw_exists(gmwid):
    """Return True if given gmwid can be retrieved from broservice, else return False."""
    try:
        gmw = _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)
    except Exception: #as err:
        err_type, err, err_traceback = _sys.exc_info()
        # if error mesage shows a non existent wellid was
        # requested, return None. Else reraise exception.
        if str(err)==f'Retrieving data from https://publiek.broservices.nl/gm/gmw/v1/objects/{gmwid} failed':
            return False
        else:
            raise
    else:
        return True


def get_gmwprops(gmwid):

        gmw = _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)
        gmwdict = gmw.to_dict()

        gmwprops = _pd.Series()
        gmwprops['broid'] = gmwdict['broId']
        gmwprops['wellcode'] = gmwdict['wellCode']

        if 'nitgCode' in gmwdict.keys():
            gmwprops['nitgcode'] = gmwdict['nitgCode']
        else:
            gmwprops['nitgcode'] = _np.nan

        gmwprops['tubecount'] = int(gmwdict['numberOfMonitoringTubes'])
        gmwprops['ownerid'] = gmwdict['owner']
        gmwprops['observerid'] = gmwdict['deliveryAccountableParty']
        gmwprops['gridreference'] = gmwdict['coordinateTransformation']
        gmwprops['registration'] = gmwdict['registrationStatus']
        if gmwdict['groundLevelPosition'] is not None:
            gmwprops['surface'] = float(gmwdict['groundLevelPosition'])
        else:
            gmwprops['surface'] = _np.nan
        gmwprops['surfacemethod'] = gmwdict['groundLevelPositioningMethod']
        gmwprops['surfacestable'] = gmwdict['groundLevelStable']
        gmwprops['mysterious_id'] = gmwdict['id']
        gmwprops['heightdatum'] = gmwdict['verticalDatum']
        gmwprops['wellconstructiondate'] = gmwdict['wellConstructionDate'].strftime('%d-%m-%Y')
        gmwprops['wellprotection'] = gmwdict['wellHeadProtector']
        gmwprops['xcr'] = round(gmwdict['deliveredLocation'].x)
        gmwprops['ycr'] = round(gmwdict['deliveredLocation'].y)
        return gmwprops


def get_tubeprops(gmwid, tube):
    """Return tubeproperties for (gmwid, tube)."""

    if not gmw_exists(gmwid):
        return _pd.Series()

    if tube not in get_gmwtubes(gmwid):
        return _pd.Series()

    # get bro tubeproperties
    gmw = _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)
    gmwdict = gmw.to_dict()
    broprops = gmwdict['monitoringTube'].loc[tube,:].squeeze()

    # get tubeproperties
    tp = _pd.Series()
    tp['startdate'] = gmwdict['wellConstructionDate'].strftime('%d-%m-%Y')
    tp['mplevel'] = broprops['tubeTopPosition']
    tp['filtop'] = broprops['screenTopPosition']
    tp['filbot'] = broprops['screenBottomPosition']
    tp['surfacelevel'] = gmwdict['groundLevelPosition']

    # float values
    for key in ['mplevel', 'filtop', 'filbot', 'surfacelevel']:
        if tp[key] is not None:
            tp[key] = float(tp[key])
        else:
            tp[key] = _np.nan

    return tp


def get_bronhouder_gmwlist(bronhouderid):
    """Return list of wellids for given bronhouderid. Returns empty list
    for invalid bronhouder id."""
    return _brodata.gmw.get_bro_ids_of_bronhouder(bronhouderid)


def get_gmwtubes(gmwid):
    """Return list of tubenumbers for gmwid."""
    gmw = _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)
    gmwdict = gmw.to_dict()
    tubenumbers = gmwdict['monitoringTube'].index.values
    return tubenumbers


def get_tubeobs_from_gmw(gmwid):
    """Return observations for each tube in a well.

    Parameters
    ----------
    gmid : str
        Valid BRO well id.

    Returns
    -------
    list
        Observations for each tube as list of GwSeries objects.
        
    """
    if not gmw_exists(gmwid):
        _warnings.warn(f'Invalid gmwid {gmwid}.')  
        return [] # no point downloading observations

    gwlist = []
    for tube in get_gmwtubes(gmwid):
         gw = get_tubeobs(gmwid, tube)
         gwlist.append(gw)

    return gwlist


def get_tubeobs(gmwid, tube):

    if not gmw_exists(gmwid):
        return GwSeries()

    gmwprops = get_gmwprops(gmwid)
    tubeprops = get_tubeprops(gmwid, tube)
    obs = _get_brodata_tubeobservations(gmwid, tube)

    gw = GwSeries()
    gw._locprops['locname']=gmwprops['broid']
    gw._locprops['filname']=tube
    gw._locprops['alias']=gmwprops['wellcode']
    gw._locprops['alias2']=gmwprops['nitgcode']
    gw._locprops['owner']=gmwprops['ownerid']
    gw._locprops['observer']=gmwprops['observerid']
    gw._locprops['constructiondate'] = gmwprops['wellconstructiondate']
    gw._locprops['xcr']=gmwprops['xcr']
    gw._locprops['ycr']=gmwprops['ycr']
    gw._locprops['height_datum']=gmwprops['heightdatum']
    gw._locprops['grid_reference']=gmwprops['gridreference']
    gw._locprops['surfacestable']=gmwprops['surfacestable']

    # tubehistory is not available in the BRO, hence 0 as index
    gw._tubeprops.loc[0,'startdate']=tubeprops['startdate']
    gw._tubeprops.loc[0,'mplevel']=tubeprops['mplevel']
    gw._tubeprops.loc[0,'filtop']=tubeprops['filtop']
    gw._tubeprops.loc[0,'filbot']=tubeprops['filbot']
    gw._tubeprops.loc[0,'surfacedate']=_np.nan
    gw._tubeprops.loc[0,'surfacelevel']=tubeprops['surfacelevel']
    
    # get head observations
    if obs.empty: # yes, wells without observations do exist.
        _warnings.warn(f'No observations for well {gmwid} tube {tube}.')
    else:

        # select regular observations
        mask1 = obs['observation_type']=='reguliereMeting'
        mask2 = obs['qualifier']!='afgekeurd'
        regobs = obs[mask1&mask2].copy()

        # get measurement datetimes
        gw._obs['headdatetime'] = regobs.index.values

        # get heads reletive to welltop
        mp = gw._tubeprops.loc[0,'mplevel']
        gw._obs['headmp'] = mp-regobs['value'].values

        # get fields headnot and remarks
        gw._obs['headnote'] = regobs['qualifier'].values
        gw._obs['remarks'] = regobs['status'].values


        # select control head observations
        mask1 = obs['observation_type']=='controlemeting'
        mask2 = obs['qualifier']!='afgekeurd'
        controls = obs[mask1&mask2].copy()

        gw._obscontrol['headdatetime'] = controls.index.values
        mp = gw._tubeprops.loc[0,'mplevel']
        gw._obscontrol['headmp']=mp-controls['value'].values
        gw._obscontrol['headnote']=controls['qualifier'].values
        gw._obscontrol['remarks']=controls['status'].values

    return gw


def get_tubeobs_within_extent(xmin=None, xmax=None, ymin=None, ymax=None):
    """Return list of GwSeries for each tube within extent (xmin, xmax, 
    ymin, ymax).
    
    Return
    ------
    xmin : int|float
        Left side of extent.

    xmax : int|float
        Right side of extent.

   ymin : int|float
        Bottom side of extent.

    ymax : int|float
        Upper side of extent.

    Returns
    -------
    List of GwSeries objects
            
    """
    tubeprops = _get_brodata_extent_tubeproperties(xmin, xmax, ymin, ymax)
    gwseries = []
    for gmwid, tube in tubeprops.index.to_flat_index().values:
        gw = get_tubeobs(gmwid, tube)
        gwseries.append(gw)
    return gwseries


def get_tubeobs_from_gmwlist(gmwids):
    """Return list of GwSeries for list of GMWids."""

    gwseries = []
    for gmwid in gmwids:
        if not gmw_exists(gmwid):
            continue
        gwlist = get_tubeobs_from_gmw(gmwid)
        if gwlist:
            gwseries.extend(gwlist)
    return gwseries


def _get_brodata_gmw(gmwid):
    """Returm brodata GroundwaterMonitoringWell instance for given gmwid."""
    return _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)


def _get_brodata_gmw_tubeproperties(gmwid):
    """Returm brodata GroundwaterMonitoringWell instance for given gmwid."""
    if not gmw_exists(gmwid):
        return _pd.DataFrame()

    gmw = _brodata.gmw.GroundwaterMonitoringWell.from_bro_id(gmwid)
    gmwdict = gmw.to_dict()
    tubeprops = gmwdict['monitoringTube']
    return tubeprops


def _get_brodata_tubeobservations(gmwid, tube):
    return _brodata.gmw.get_tube_observations(gmwid, tube)


def _get_brodata_extent_gmwproperties(xmin, xmax, ymin, ymax):
    """Return gmw properties for all well in extent (xmin, xmax, ymin, ymax)."""
    extent = [xmin, xmax, ymin, ymax]
    gdf = _brodata.gmw.get_characteristics(extent=extent)
    return gdf


def _get_brodata_extent_tubeproperties(xmin, xmax, ymin, ymax):
    """Return tube properties for all tubes in extent (xmin, xmax, ymin, ymax)."""
    extent = [xmin, xmax, ymin, ymax]
    gdf = _brodata.gmw.get_characteristics(extent=extent)
    tube_gdf = _brodata.gmw.get_tube_gdf_from_characteristics(gdf)
    return tube_gdf


def _get_brodata_extent_observations(xmin, xmax, ymin, ymax):
    """Return geodataframe with all tubeobservations in extent (xmin, xmax, ymin, ymax)."""
    extent = [xmin, xmax, ymin, ymax]
    gdf = _brodata.gmw.get_data_in_extent(
        extent=extent, kind="gld", combine=True, as_csv=True
        )
    return gdf


