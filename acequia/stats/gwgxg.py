""" This module contains a class GwGxg that calculates some
descriptive statistics from a series of groundwater head measurements
used by groundwater practitioners in the Netherlands 

Author: Thomas de Meij (who borrowed lavishly from Pastas dutch.py)

"""

import numpy as np
import pandas as pd

class GxG:
    """Calculate descriptive statistics from measured heads"""

    def __init__(self, gw):

        #if not isinstance(gw,GwSeries):
        #    raise TypeError("Expected a GwSeries, got {}".format(
        #        type(gw)))
        self._gw = gw

