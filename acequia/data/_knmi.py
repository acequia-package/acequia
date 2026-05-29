

from importlib import resources as _resources
import pandas as _pd
import geopandas as _gpd

from . import _knmi_data

def knmi_weatherstations(geo=True):
    
    # read file
    srcfile = (_resources.files(_knmi_data) / 'hydropandas_knmi_meteostation.json')
    meteo = _pd.read_json(srcfile)
    meteo.index.name = 'stn'
    meteo = meteo.rename(columns={'x':'xcr', 'y':'ycr', 'hoogte':'height', 'naam':'stn_name'})

    # reorder columns
    columns = ['stn_name','xcr','ycr','height','lon','lat']
    unexpected = [x for x in meteo.columns if x not in columns]
    meteo = meteo[columns+unexpected].sort_values('stn_name')

    if geo:
        meteo = _gpd.GeoDataFrame(
            meteo, 
            geometry=_gpd.points_from_xy(meteo.xcr, meteo.ycr), 
            crs="EPSG:28992"
            )

    return meteo

def knmi_raingauches(geo=True):

    # read file
    srcfile = (_resources.files(_knmi_data) / 'hydropandas_knmi_neerslagstation.json')
    rain = _pd.read_json(srcfile)
    rain.index.name = 'stn'
    rain = rain.rename(columns={'x':'xcr','y':'ycr', 'hoogte':'height', 'naam':'stn_name'})

    # reorder columns
    columns = ['stn_name', 'xcr', 'ycr', 'height', 'lon', 'lat']
    unexpected = [x for x in rain.columns if x not in columns]
    rain = rain[columns+unexpected].sort_values('stn_name')

    if geo:
        rain = _gpd.GeoDataFrame(
            rain, 
            geometry=_gpd.points_from_xy(rain.xcr, rain.ycr), 
            crs="EPSG:28992"
            )

    return rain
