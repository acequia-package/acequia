
#print(f'Loading package {__name__}')

import logging

from .gwseries import GwSeries
from .gwlist import GwList
from .gwlist import headsfiles as headsfiles
from .gwlocs import GwLocs
from .headsdif import HeadsDif
from .headsdif import headsdif_from_gwseries as headsdif_from_gwseries
from .geo.coordinate_conversion import CrdCon
from .geo.waypoint_kml import WpKml
from .geo.pointshapewriter import PointShapeWriter, pointshape_write
from .plots.plotheads import PlotHeads
from .plots.tsmodelstatsplot import TsModelStatsPlot,plot_tsmodel_statistics
from .read.dinogws import DinoGws, read_dinogws
from .read.hydromonitor import HydroMonitor
from .read.knmi_stations import KnmiStations, knmilocations
from .read.filedirtools import listdir, cleardir
from .stats.utils import hydroyear, season, index1428, ts1428
#from .stats.gwstats import GwStats
from .stats.timestats import TimeStats, timestats
from .stats.gxg import Gxg, stats_gxg
from .stats.quantiles import Quantiles
from .stats.describe import DescribeGwList, timestatstable

__all__ = ['GwSeries','GwList','GwLocs','PlotGws','DinoGws',
           'HydroMonitor','TimeStats','PointShapeWriter','Gxg','Quantiles','CrdCon',
           'KnmiStations','DescribeGwList','timestatstable','pointshape_write'
           'TsModelStatsPlot','plot_tsmodel_statistics']

logger = logging.getLogger(__name__)
