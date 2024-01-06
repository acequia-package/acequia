
import numpy as np
from pandas import DataFrame, Series
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib as mpl

from .._core.gwseries import GwSeries

def plot_tubechanges(gw=None, ax=None, headnotes=None):
    """Time series plot of heads and tube changes.
    
    Parameters
    ----------
    gw : GwSeries
        Groundwater heads and tube properties.
    ax : 

    Returns
    -------
    ax
    """
    headsdotclr = '#0000ff' #'#3e92d1'
    headslineclr = '#0080ff'
    welltopclr = '#f44336'
    srfclr = 'gray'
    filbotclr = '#6a329f'

    #if not isinstance(gw,GwSeries):

    # plot groudnwater heads
    heads = gw.heads(ref='datum')
    heads.dropna().plot(ax=ax, color=headslineclr, label='stijghoogte',
        lw=1., marker='.', markersize=5., markerfacecolor=headsdotclr,)

    # plot well tube changes
    tubeprops = gw.tubeprops()
    mp = gw.tubeprops_changes(proptype='mplevel',relative=False)
    sf = gw.tubeprops_changes(proptype='surfacelevel',relative=False)
    fb = gw.tubeprops_changes(proptype='filbot',relative=False)

    mp.plot(ax=ax,color=welltopclr,label='bovenkant buis',)
    fb.plot(ax=ax,color=filbotclr,label='onderkant filter')
    sf.plot(ax=ax,color=srfclr,label='maaiveld',linestyle='--')

    # plot missing head notes
    if headnotes:
        notes = gw.get_headnotes(kind=headnotes)
        for date in notes.index.values:
            x = date
            yaxmax = ax.get_ylim()[1]
            y = yaxmax - 0.05
            note = notes[date]
            ax.text(x, y, note, fontsize=7., color=headsdotclr)

    # format x-ax labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    ax.set_xlabel('')
    ax.xaxis.set_major_locator(mdates.YearLocator(3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    #mpdate = fb.index[0]

    # plot vertical lines at welltube change dates with text
    for idx,row in gw.tubeprops().iterrows():
        ax.axvline(x=row['startdate'], color="gray", linestyle=":")

        xmin, xmax = ax.get_xlim()
        deltadays = pd.Timedelta(days=round((xmax-xmin)*0.02))
        x = row['startdate'] - deltadays

        dy = (row['mplevel']-row['filbot'])*0.05
        y = row['filbot'] + dy

        text = row['startdate'].strftime('%d-%m-%Y')
        ax.text(x, y, text, rotation='vertical', fontsize='small')

    # plot vertical line after last observation
    ##x = heads.index[-1]
    x = gw._obs.loc[gw._obs.index[-1], 'headdatetime'] # last observation date
    text = x.strftime('%d-%m-%Y')
    ax.axvline(x=x,color="gray", linestyle=":")
    ax.text(x-deltadays, y, text, rotation='vertical', fontsize='small')

    # plot legend and title
    ax.legend(loc='upper center',bbox_to_anchor=(0.5, -0.15), ncol=4,
        prop={'size':9.})
    ax.set_title(gw.name(),fontdict={'fontsize':11.},loc='left')
    
    return ax
