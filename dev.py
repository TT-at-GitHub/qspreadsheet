#In[0]
import sys, os
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import numpy as np
import numpy
import pandas as pd 

from fx import fx

import PySide2
plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
#In[0]
area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
population = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
population = population.astype(float)
states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
df = pd.DataFrame({'states':states, 'area':area, 'population':population}, index=range(len(states)))
dates = [pd.to_datetime('06-15-2020') + pd.DateOffset(i) for i in range(1, df.shape[0] + 1)]
df['dates'] = dates
df['bools'] = (df.index % 2 == 1)
df['multip'] = df.population * 3.42 * df['bools']
df['div'] = df.population / 2.3 * (~df['bools'])
df['multip'] = (df['multip'] + df['div']).astype('float32')
df['div'] = df['div'].astype(int)
df.dtypes
#In[0]
df.dtypes.map(str).str.contains('float')

#In[0]
df['dates'] = dates
df
#In[0]
df.population = df.population.astype('int32')
df.dtypes
#In[0]
df.select_dtypes(include=['float32', 'float64'])