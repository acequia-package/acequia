"""Acequia is a python package for processing hydrological data."""


import logging as _logging

from . import _read
from . import data
from . import io
from . import _brodata
from . import plot

from ._core.gwseries import GwSeries
from ._core.gwcollection import GwCollection
from ._core.gwlist import GwList
from ._core.gwlocs import GwLocs

from ._read.gwfiles import GwFiles

from ._core.headsdif import HeadsDif
from ._core.swseries import SwSeries

##from ._geo.waypoint_kml import WpKml
##from .io.pointshapewriter import PointShapeWriter
##from ._geo.gpxtracklog import GpxTracklog

from ._plots.plotheads import PlotHeads
from ._plots.tsmodelstatsplot import TsModelStatsPlot
from .io._dinogws_csv import DinoGwsCsv

from ._read.dinosurfacelevel import DinoSurfaceLevel
from .io._dawaco import Dawaco
##from ._read.gpxtree import GpxTree
##from ._read.hydromonitor import HydroMonitor
from .io._waterweb import WaterWeb
from ._read import filetools as _filetools
from .io._brorest import BroREST
#from .io._brogldxml import BroGldXml
#from .io._brogmwxml import BroGmwXml
from .io._brogwseries import BroGwSeries
from .io._brogwcollection import BroGwCollection

from ._stats.gwtimestats import GwTimeStats
from ._stats.gxg import GxgStats
from ._stats.quantiles import Quantiles
from ._stats.meteo_drought import MeteoDrought

from ._core.version import __version__

_logging.getLogger('acequia') #.addHandler(logging.NullHandler())

