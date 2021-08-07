#
# 12-01-2020 Testing GwSeries JSON esport and import
# Thomas de Meij
#
import os
import json
import collections
from pandas import Series, DataFrame
import pandas as pd
import numpy as np


from acequia import GwSeries, DinoGws
import acequia as aq


if __name__ == '__main__':


    if 1: 

        """read multiple dinoloket files with groundwater data
           to gwseries object, export as json and read back"""
    
        dinodir = r".\testdata\dinogws\\"
        jsondir = r".\output\json\\"

        dinofiles = [f for f in os.listdir(dinodir) 
                     if os.path.isfile(os.path.join(dinodir,f)) 
                     and f[11:13]=="_1"]

        for i,srcfile in enumerate(dinofiles):
        
            print("processing file ",srcfile)

            # read from dinocsv
            gws = GwSeries.from_dinogws(dinodir+srcfile)

            # write to json file
            jstr = gws.to_json(dirpath=jsondir)

            # read back from json file
            sourcepath = jsondir+gws.name()+'.json'
            json_dict = GwSeries.from_json(filepath=sourcepath)

