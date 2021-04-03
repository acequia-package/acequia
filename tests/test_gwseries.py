"""
 testing module gwseries from acequia

"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

import acequia as aq
from acequia import GwSeries
from acequia import DinoGws

def hdr(msg):
    print()
    print('#','-'*50)
    print(msg)
    print('#','-'*50)
    print()


if __name__ == '__main__':

    dinodir = '.\\testdata\\dinogws\\'
    dinogwstestfilepath = f'{dinodir}B29A0850002_1.csv'
    jsontestfilepath = '.\\testdata\\json\\B29A0850_2.json'
    jsonoutdir = '.\\output\\json\\'
    csvoutdir = '.\\output\\csv\\'
    plotsdir = f'.\\output\\plots\\'

    # B29A0848 (n=3)

    if 1: 

        hdr('# test GwSeries() (create empty GwSeries object)')

        gw = GwSeries()
        print('Result: ',gw)


    if 1: 

        hdr('# test GwSeries.from_dinogws()')

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)
        print('Result: ',gw)


    if 1:

        hdr('# test GwSeries.from_json()')

        filepath = jsontestfilepath
        gw = GwSeries.from_json(filepath)
        print('Result: ',gw)


    if 1: 

        hdr('# test GwSeries.to_json()')

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)
        jdict = gw.to_json(jsonoutdir)

        locname = jdict['locprops']['locname']
        print(f'Result: jdict for {locname}')
        for key in jdict:
            print(f'{key} {len(jdict[key])}')


    if 1: 

        hdr('# test GwSeries.to_csv()')

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)
        series = gw.to_csv(csvoutdir)

        if isinstance(series,pd.Series):
            locname = series.name
            print(f'Result: {locname} n={len(series)}')
        else:
            print(f'Result: {type(series)}')




    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.name()')
        print(gw.name())

        hdr('# test GwSeries.locname()')
        print(gw.locname())


    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.locprops()')
        sr = gw.locprops(minimal=False)
        print(sr)

        hdr('# test GwSeries.tubeprops()')
        sr = gw.tubeprops()
        print(sr)

        hdr('# test GwSeries.tubeprops(last=True)')
        sr = gw.tubeprops(last=True)
        print(sr)

        hdr('# test GwSeries.surface()')
        print(f'Surface level is {gw.surface()}')


    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.heads()')
        sr = gw.heads()
        print(f'number of measured heads is {len(sr)}')


    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.timestats()')
        print(gw.timestats())


    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.describe()')
        print(gw.describe(gxg=True))



    if 1: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.tubeprops_changes()')
        print(gw.tubeprops_changes())


    if 0: 

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.plotheads()')
        filepath = f'{plotsdir}{gw.name()}.jpg'
        gw.plotheads(proptype='mplevel',filename=filepath)

    if 1:

        filepath = dinogwstestfilepath
        gw = GwSeries.from_dinogws(filepath)

        hdr('# test GwSeries.gxg()')
        gxg = gw.gxg(reflev='surface')
        print(gxg)

