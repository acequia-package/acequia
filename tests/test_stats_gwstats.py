

"""
    Test GwStats object 

"""

import os
import os.path
from importlib import reload

import acequia as aq
reload(aq)
from acequia import GwSeries
from acequia import GwStats
#reload(aq.GwStats)

import acequia.gwseries
reload(acequia.gwseries)

import acequia.stats.gwstats
reload(acequia.stats.gwstats)

print(__name__)

if __name__ == '__main__':

    sourcedir = ".\\testdata\\dinogws\\"
    srcfile = "B28A0475002_1.csv"
    gw = aq.GwSeries.from_dinogws(sourcedir+srcfile)
    sr = gw.heads(ref='datum')
    index = gw.dates1428()
    #sr.index[sr.index.get_loc(index, method='nearest')]
    sr3 = gw.heads1428(maxlag=3)
    



    if 0: # test all seperate methods of class acequia.stats.gwstats()
        
        # test empty init
        gst = GwStats()
        print("length series is: "+str(len(gst.series()))+" (after empty init).")
        
        # test method reset
        gst.reset()
        print("length series is: "+str(len(gst.series()))+" (after reset).")

        # test init with series
        gst = GwStats(sr, ref="cmmv")
        print("length series is: "+str(len(gst.series())))
        
        # test method series14
        ts14 = gst.series14()
        print("length series with fourteen day values is: "+str(len(ts14)))
    
        # test method stat()
        dfstat,dfsumstats,dfgvgdiff,ts,ts14 = gst.stats()
        print("length dfstat is: "+str(len(dfstat)))
        print("length dfsumstats is: "+str(len(dfsumstats)))
        print("length dfgvgdiff is: "+str(len(dfgvgdiff)))
        print("length ts is: "+str(len(ts)))
        print("length ts14 is: "+str(len(ts14)))

        # test method quantiles()
        dfqt = gst.quantiles()
        print("length dfqt is: "+str(len(dfqt)))

        # test method tables() & save as csv
        dfhg3,dfgxg,dfgvgdiff = gst.tables()
        print("length dfhg3 is: "+str(len(dfhg3)))
        print("length dfgxg is: "+str(len(dfgxg)))
        
        outfile = ".\\output\\xg3test.csv"
        dfhg3[dfhg3["n"]>gst.minN14].to_csv(outfile,index=False,date_format="%d-%m-%Y")
        print("Saved xg3test.csv")

        outfile = ".\\output\\gxgtest.csv"
        dfgxg.to_csv(outfile,index=False,date_format="%d-%m-%Y")
        
        print("Saved gxgtest.csv")        
        
        # test method to_excel & to_excel_fast
        # see below for test with multiple files
        #gst.to_excel(".\\output\\data.xlsx")
        #print("Saved data.xlsx")        
        gst.to_excel_fast(".\\output\\data-fast.xlsx")        
        print("Saved data-fast.xlsx")
        
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


            #sr = dn.series(units="cmnap")
            
            # setseries
            gst = GwStats(sr, ref="cmmv")
            
            # export statistics to excel
            if len(sr[sr.notnull()])>0:
            
                # test to_excel_fast
                outfile = xlsxdir+srcfile[:11]+"-fast.xlsx"
                wb = gst.to_excel_fast(outfile)
                
                # test to_excel
                #outfile = xlsxdir+srcfile[:11]+".xlsx"
                #wb = gst.to_excel(outfile)

            # calculate lists of statistics
            dfstat,dfsumstats,dfgvgdiff,ts,ts14 = gst.stats()
            if i==0: 
                dfsumlist = dfsumstats
                dfgvglist = dfgvgdiff
            else: 
                dfsumlist = dfsumlist.append(dfsumstats, ignore_index=True,sort=True)
                dfgvglist = dfgvglist.append(dfgvgdiff, ignore_index=True,sort=True)
           
 
