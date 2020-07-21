#In[0]
import sys, os
from PyQt5.QtCore import center
import numpy as np
import pandas as pd 
import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

#In[0]
area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
data = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
data.area = data.area.astype(float)
data
#In[0]
data.area = data.area.astype(str)

data.dtypes