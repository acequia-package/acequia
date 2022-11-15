
import numpy as np
from pandas import DataFrame, Series
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from acequia import GwSeries

def plot_tubechanges(gw=None,ax=None):
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
    headsclr = '#3e92d1'
    welltopclr = '#f44336'
    srfclr = 'gray'
    filbotclr = '#6a329f'

    #if not isinstance(gw,GwSeries):

    heads = gw.heads(ref='datum')
    tubeprops = gw.tubeprops()
    mp = gw.tubeprops_changes(proptype='mplevel',relative=False)
    sf = gw.tubeprops_changes(proptype='surfacelevel',relative=False)
    fb = gw.tubeprops_changes(proptype='filbot',relative=False)

    heads.plot(ax=ax,color=headsclr,label='stijghoogte')
    mp.plot(ax=ax,color=welltopclr,label='bovenkant buis',)
    fb.plot(ax=ax,color=filbotclr,label='onderkant filter')
    sf.plot(ax=ax,color=srfclr,label='maaiveld',linestyle='--')

    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    ax.set_xlabel('')

    ax.xaxis.set_major_locator(mdates.YearLocator(3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    ax.legend(loc='upper center',bbox_to_anchor=(0.5, -0.15), ncol=4,
        prop={'size':9.})
    ax.set_title(gw.name(),fontdict={'fontsize':11.},loc='left')

    mpdate = fb.index[0]

    for idx,row in gw.tubeprops().iterrows():
        plt.axvline(x=row['startdate'],color="gray", linestyle=":")

        dx = pd.Timedelta(days=250)
        x = row['startdate']-dx
        dy = (row['mplevel']-row['filbot'])*0.05
        y = row['filbot']+dy
        text = row['startdate'].strftime('%d-%m-%Y')
        plt.text(x,y,text,rotation='vertical',fontsize='small')

    x = heads.index[-1]
    text = heads.index[-1].strftime('%d-%m-%Y')
    plt.axvline(x=x,color="gray", linestyle=":")
    plt.text(x-dx,y,text,rotation='vertical',fontsize='small')
    
    return ax
