

"""
    Test GwSerieres object 

"""

import os
import os.path
from importlib import reload

import acequia as aq
reload(aq)
#from acequia import GwSeries
#from acequia import GwStats
#reload(aq.GwStats)

import acequia.gwseries
reload(acequia.gwseries)

#import acequia.stats.gwstats
#reload(acequia.stats.gwstats)

import clsDINOGWS
reload(clsDINOGWS)

print(__name__)

if __name__ == '__main__':

    sourcedir = ".\\testdata\\dinogws\\"
    srcfile = "B28A0475002_1.csv"
    dn = clsDINOGWS.dinogws(filepath=sourcedir+srcfile)
    gws = aq.GwSeries.from_dinogws(sourcedir+srcfile)
    sr = gws.heads(ref='datum')

    if 1:

        print('test empty header file')


        # create dinofile object for testing
        sourcedir = ".\\testdata\\dinogws\\"  
        filepath = sourcedir+'B17C0296001_1.csv'
        dn2 = clsDINOGWS.dinogws(filepath=filepath)

        # create gwseries from dinofile
        gw = acequia.GwSeries.from_dinogws(filepath)


    if 0: # test methods for multiple dino files in a directory
    
        sourcedir = ".\\testdata\\dinogws\\"
        outputdir = ".\\output\\" 
        xlsxdir   = ".\\output\\" 
        filenames = [f for f in os.listdir(sourcedir) if os.path.isfile(os.path.join(sourcedir,f)) and f[11:13]=="_1"]
        
        for i,srcfile in enumerate(filenames):
        
            print("processing file ",srcfile)
        
            # getseries
            ##dn = clsDINOGWS.dinogws()
            ##dn.readfile(sourcedir+srcfile,readdata=True)

            ##sourcepath = ".\\testdata\\dinogws\\"+"B28A0475002_1.csv"
            gws = aq.GwSeries.from_dinogws(sourcedir+srcfile)
            sr = gws.heads(ref='datum')

           
 
