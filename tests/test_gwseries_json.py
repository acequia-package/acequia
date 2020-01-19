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


    if 1: # read multiple dinoloket files with groundwater data
          # to gwseries object, export as json and read back
    
        sourcedir = r".\testdata\dinogws\\"
        filenames = [f for f in os.listdir(sourcedir) 
                     if os.path.isfile(os.path.join(sourcedir,f)) 
                     and f[11:13]=="_1"]
        jsondir = r".\output\json\\"

        for i,srcfile in enumerate(filenames):
        
            print("processing file ",srcfile)

            gws = GwSeries.from_dinogws(sourcedir+srcfile)
            jstr = gws.to_json(dirpath=jsondir)
            sourcepath = jsondir+gws.name()+'.json'
            json_dict = GwSeries.from_json(filepath=sourcepath)
