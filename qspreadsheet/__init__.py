import os
import PySide2
from typing import TypeVar

import numpy as np
import pandas as pd 


LEFT, ABOVE = range(2)

DF = TypeVar('DF', bound=pd.DataFrame)
SER = TypeVar('SER', bound=pd.Series)

plugin_path = os.path.join(os.path.dirname(
    PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from . import resources_rc
from .custom_widgets import *
from .sort_filter_proxy import *
from .delegates import *
from .qspreadsheet import *