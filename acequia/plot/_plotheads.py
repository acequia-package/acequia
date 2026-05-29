
#import numpy as np
#from pandas import Series, DataFrame
#import pandas as pd
import matplotlib.pyplot as _plt


def plot_multiple_heads_with_difference(gwlist, figtitle=None, startdate=None, enddate=None, plotsurface=None, namefield=None, linecolors=None):
    """Plot groundwater heads in mNAP in one graph and head differences
    with first series in seperate graphs below main graph.
    
    gwlist : list of GwSeries objects
        GwSeries objects with level data.

    figtitle : str
        Title plotted above figure.

    startdate : str, default None
        Startdate for time series, measurements before this date 
        will be ignored. Format "YYYY-MM-DD".

    enddat : str, optional
        Enddate for time series.

    plotsurface : int|None, default None
        Plot horzontal line at level plotsurface.

    namefield : str, optional
        GwSeries locprops field to use for series name.

    linecolors : list of str, optional
        List of hexcolor codes for plotting head series and differences.
    
    Returns
    -------
    ax with graph.
            
    """
    if linecolors is None:
        linecolors = ['#330077','#ba232c','#23bab1', '#b123ba', '#bab123',]

    #if startdate|enddate:
    #    if not enddate:

    # create figure
    nrows = len(gwlist)

    figwidth=9
    upper_figheight = 4
    lower_figheight = 1 # 2inch
    number_of_lower_figs = nrows-1
    figheight = upper_figheight + lower_figheight*number_of_lower_figs
    height_ratios = [upper_figheight/figheight] + [((lower_figheight*number_of_lower_figs)/figheight)/number_of_lower_figs]*number_of_lower_figs
    fig, axes = _plt.subplots(
        nrows=nrows, ncols=1, sharex=True, 
        figsize=(figwidth, figheight),
        gridspec_kw={'width_ratios': [1], 'height_ratios': height_ratios,
            'wspace': 0.01, 'hspace': 0.05},
        )

    # plot heads in main graph
    for i, gw in enumerate(gwlist):

        # get properties from gwseries object
        tp = gw.tubeprops()
        filbot = tp.loc[tp.index[0], 'filbot']
        if i==0:
            surface = tp.loc[tp.index[0], 'surfacelevel']
        
        if namefield is None:
            wellname = gw.name()
        else:
            wellname = gw.locprops().loc[gw.locname(), namefield]

        # plot heads
        heads = gw.heads().resample('D').mean().dropna()
        heads = heads[startdate:enddate].copy()
        label = f'{wellname} (filbot {filbot} mnap / {round((filbot-surface),2)} mv)'
        axes[0].plot(heads.index.values, heads.values, label=label, color=linecolors[i], linewidth=1.)

        # reverse plotting order of lines
        lines = axes[0].get_lines()
        for i, line in enumerate(lines, -len(lines)):
            line.set_zorder(abs(i))

    # plot head differences below main graph
    for i, gw in enumerate(gwlist):
        if (i>0) & (len(gwlist)>i-1):
            heads = gw.heads().resample('D').mean().dropna()
            headsref = gwlist[0].heads().resample('D').mean().dropna()
            sr = (heads-headsref)[startdate:enddate].copy()
            axes[i].plot(sr.index.values, sr.values, linewidth=0, marker='o', markersize=3., color=linecolors[i])
            ymin, ymax = axes[i].get_ylim()
            ymin=-0.055 if ymin>-0.055 else ymin
            ymax=+0.055 if ymax<0.055 else ymax
            axes[i].set_ylim(ymin, ymax)

            # draw 0-line
            axes[i].axhline(y=0, linestyle='--', color='#808080')

    if figtitle:
        axes[0].text(0.01, 1.025, figtitle, horizontalalignment='left',
            verticalalignment='baseline', transform=axes[0].transAxes,
            fontsize=14.)

    if plotsurface is None:
        plotsurface=surface
    axes[0].axhline(y=plotsurface, linestyle='--', color='#808080')

    #axes[0].subplots_adjust(left=0.05)
    #axes[0].legend(loc='lower left')
    fig.legend(ncol=2, loc="lower left", bbox_to_anchor=(0.05, 0.01)) 

    axes[0].set_ylabel('Grondwaterstand (mNAP)', fontsize=8.)

    #fig.tight_layout()
    #fig.constrained_layout()
    _plt.subplots_adjust(left=0.07, bottom=0.15, right=0.99, top=0.95, wspace=0.05, hspace=0.05)
    
    return axes
