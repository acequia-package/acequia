

"""
    Test GwSeries object 

"""

import os
import os.path
from importlib import reload

import acequia as aq


if __name__ == '__main__':

    sourcedir = ".\\testdata\\dinogws\\"
    srcfile = "B28A0475002_1.csv"
    gws = aq.GwSeries.from_dinogws(sourcedir+srcfile)
    sr = gws.heads(ref='datum')

    if 1: # test methods for multiple dino files in a directory
    
        sourcedir = ".\\testdata\\dinogws\\"
        filenames = [f for f in os.listdir(sourcedir) 
                     if os.path.isfile(os.path.join(sourcedir,f)) 
                     and f[11:13]=="_1"]
        
        for i,srcfile in enumerate(filenames):
        
            print("processing file ",srcfile)

            gws = aq.GwSeries.from_dinogws(sourcedir+srcfile)
            sr = gws.heads(ref='datum')

    if 1:

        print('test empty header file')


        # create dinofile object for testing
        sourcedir = ".\\testdata\\dinogws_fouten\\"  
        filepath = sourcedir+'B17C0296001_1.csv'

        # create gwseries from dinofile
        gw = aq.GwSeries.from_dinogws(filepath)

