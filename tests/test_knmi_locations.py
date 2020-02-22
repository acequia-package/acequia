
import acequia as aq
from acequia import KnmiLocations

if 1: # test KnmiLocations.prec_stns()

    knmi = KnmiLocations()
    
    print("Retrieving list of all available precipitation stations.")
    #filepath = r'..\02_data\knmi_locations\stn-prc-available.csv'
    filepath = 'stn-prc-available.csv'
    dfprc = knmi.prec_stns(filepath)
    print(f'{len(dfprc)} precipitation stations available on KMNI website.')
    print()

if 1: # test KnmiLocations.wheater_stns()

    knmi = KnmiLocations()
    print("retrieving list of all available weather stations.")
    #filepath = r'..\02_data\knmi_locations\stn-wht-available.csv'
    filepath = 'stn-wht-available.csv'
    dfwht = knmi.weather_stns(filepath)
    print(f'{len(dfwht)} weather stations available on KMNI website.')
    print()

if 1: # test KnmiLocations.prec_coords()

    knmi = KnmiLocations()
    print("Reading coordinates of prcipitation stations from file.")
    #datadir = datadir = r'..\02_data\knmi_locations\\'
    filepath = 'stn-prc-available.csv'
    dfcrd = knmi.prec_coords(filepath)
