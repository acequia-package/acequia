
import matplotlib.pyplot as plt
from pandas import Series, DataFrame
import pandas as pd
import acequia as aq


def message(message):
    """ function for printing message to screen """
    print()
    print("-"*len(message))
    print(message)
    print("-"*len(message))
    print()


if 1:

    srcdir = r'.\testdata\json\\'
    plotsdir = r'.\output\plots\\'

    # read four time series of one well location

    sourcefile = srcdir+'B29A0850_1.json'
    gw1 = aq.GwSeries.from_json(sourcefile)
    sr1 = gw1.heads(ref='datum')

    sourcefile = srcdir+'B29A0850_2.json'
    gw2 = aq.GwSeries.from_json(sourcefile)
    sr2 = gw2.heads(ref='datum')

    sourcefile = srcdir+'B29A0850_3.json'
    gw3 = aq.GwSeries.from_json(sourcefile)
    sr3 = gw3.heads(ref='datum')

    sourcefile = srcdir+'B29A0850_4.json'
    gw4 = aq.GwSeries.from_json(sourcefile)
    sr4 = gw4.heads(ref='datum')


    # read series with changes in reference height

    sourcefile = r'.\testdata\dinogws\B29C0191001_1.csv'
    gw5 = aq.GwSeries.from_dinogws(sourcefile)
    sr5 = gw5.heads(ref='datum')

    gw6 = aq.GwSeries.from_dinogws(sourcefile)
    sr6 = gw6.heads(ref='surface')

if 0:

    # --------------------------------
    # test PlotHeads() with one series
    # --------------------------------

    plot = aq.PlotHeads(ts=[sr3],ylim=[19.5,21.5])

if 0:

    # -------------------------------------
    # test PlotHeads() with multiple series
    # -------------------------------------

    plot = aq.PlotHeads(ts=[sr1,sr2,sr3,sr4])
    outpath = f'{plotsdir}{plot.ts[0].name}.png'
    plot.save(outpath)


if 1:

    # --------------------------------------------
    # test PlotHeads() with reference change graph
    # --------------------------------------------

    plot = aq.PlotHeads(ts=[sr5])

    mps = gw5.tubeprops_changes()
    plot = aq.PlotHeads(ts=[sr5],mps=mps)

    mps = gw5.tubeprops_changes(proptype='surfacelevel')
    plot = aq.PlotHeads(ts=[sr5],mps=mps)

    mps = gw5.tubeprops_changes(proptype='filbot')
    plot = aq.PlotHeads(ts=[sr5],mps=mps)

if 1:

    # ---------------------------------------------------
    # test PlotHeads() for heads relative to surfacelevel
    # ---------------------------------------------------

    mps = gw5.tubeprops_changes(proptype='surfacelevel')
    plot = aq.PlotHeads(
                ts=[sr6],ref='surface', mps=mps)


if 0:

    # ---------------------------------------------------
    # test PlotHeads() for all locations in testdata
    # ---------------------------------------------------

    srcdir = f'.\\testdata\\dinogws\\'
    plotdir = f'.\\output\\plots\\'
    locnames = ['B12A1806','B29A0848','B32E1199']
    locs = aq.GwLocs(filedir=srcdir,groups=locnames)
    for i,loc in enumerate(locs):

        for ts in loc:
            ts.heads().plot()

        locname = loc[0].locname()
        plot = aq.PlotHeads(ts=loc,ref='datum',title=locname)
        plot.save(f'{plotdir}{locname}.jpg')
        #plt.close()

if 0:
    sr1 = dn1.series(units="cmmv")
    desc1 = dn1.describe()

    # test pplotseries : twee meetreeksen
    message("Test plotseries with sbb ref point DRAn-B601a.2   ")

    plot = plotseries()

    plot.plotseries(ts=[sr1],description=[desc1],reference="cmmv",xlim=['01-01-1997','14-11-1999'],
        ylim=[-50,200], title="Test: SBBRefpunt DRAn-601a.2")
    plot.saveplot('.\\output\\test plotseries\\test-sbbref.png')
    plt.show()


if 0:

    dn1 = dinogws()
    dn1.readfile(r".\testdata\B34D0081001_1.csv")

    dn2 = dinogws()
    dn2.readfile(r".\testdata\B34D0081002_1.csv")

    sr1 = dn1.series(units="cmnap")
    sr2 = dn2.series(units="cmnap")

    desc1 = dn1.describe()
    desc2 = dn2.describe()

    # test pplotseries : twee meetreeksen
    message("Test plotseries with two series   ")

    #plt.rcParams['figure.figsize'] = [5, 3]

    myplotargs = [
        {'color':'#2347c5', 'marker':'o', 'linestyle':'dashed',
         'linewidth':1, 'markersize':4},
        {'color':'#b41515', 'marker':'o', 'linestyle':'solid', 
         'linewidth':1, 'markersize':4}]

    plot = plotseries()
    plot.plotseries(ts=[sr1,sr2],description=[desc1,desc2], 
                    xlim=[1955,2005], ylim=[1500,1800], 
                    title="Test: Twee meetreeksen",
                    plotargs = myplotargs)
    plot.saveplot('.\\output\\test plotseries\\test twee meetreeksen.png')
    plt.show()

if 0:

    # test plotseries 

    # read data to series

    dn1 = dinogws()
    dn1.readfile(r".\testdata\B12B0297001_1.csv")
    sr1 = dn1.series(units="cmmv")
    desc1 = dn1.describe()

    # test pplotseries : twee meetreeksen
    message("Test plotseries with sbb ref point DRAn-B601a.2   ")

    plot = plotseries()

    plot.plotseries(ts=[sr1],description=[desc1],reference="cmmv",xlim=['01-01-1997','14-11-1999'],
        ylim=[-50,200], title="Test: SBBRefpunt DRAn-601a.2")
    plot.saveplot('.\\output\\test plotseries\\test-sbbref.png')
    plt.show()

if 0:

    # test plotseries : één reeks met referentielijn
    message("Test plotseries with reference line   ")

    ref = dn1.mpref()
    plot = plotseries()
    plot.plotseries(ts=[sr1],description=[desc1], title="Test: Meetreeks met referentielijn", mps=ref)
    plot.saveplot('.\\output\\test plotseries\\test meetreeks-met-referentie.png')
    plt.show()


if 0: # test plotduurlijn
    if dn1.frq(): plot.plotduurlijn(dn1.frq)
    plot.saveplot('duurlijn.png')
    plt.show()


if 0: 
    if dn.frq(): 
        plot.plotduurlijn(dn.frq)
        plot.saveplot('duurlijn.png')
        plt.show()        


if 0: # test functions for all files in directory with test files (with many problems)

    sourcedir = ".\\testdata\\"           
    filenames = [f for f in os.listdir(sourcedir) if os.path.isfile(os.path.join(sourcedir,f)) and f[11:13]=="_1"]
    for i,srcfile in enumerate(filenames):

        dn = dinogws(sourcedir+srcfile)
        plot = plotseries()
        #dn.readfile(sourcedir+srcfile)
        if len(dn.series())!=0:
            sr = dn.series(units="cmnap")
            ref = dn.mpref()
            plot.plotseries(ts=[sr],mps=ref, title=srcfile)
            plot.saveplot(".\\output\\log\\graph\\"+srcfile.split(".")[0]+".png")
            plt.show()
            plt.close()

print ("Script finished")