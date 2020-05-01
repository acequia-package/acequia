
import acequia as aq
import os

if 1:

    dndir = 'D:\\data\\DINO2020\\'

    filelist = [
        'B22D0138001_1.csv','B22D0138002_1.csv','B22D0138003_1.csv'
        ]
    for i,dnfile in enumerate(filelist):
        sourcefile = os.path.join(dndir,dnfile)
        gw = aq.GwSeries.from_dinogws(sourcefile)
        sr = gw.heads(ref='datum')
        if i==0:
            tslist = [sr]
        else:
            tslist = tslist+[sr]
    plot = aq.PlotHeads(ts=tslist,ylim=[5,8])


    #outpath = f'..\\03_results\\{plot.ts[0].name}.png'
    outpath = f'{plot.ts[0].name}.png'
    plot.save(outpath)