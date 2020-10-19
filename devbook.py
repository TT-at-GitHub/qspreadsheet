# dev_data.py
#In[0]
import os, sys
import random
import string
from PySide2.QtWidgets import QApplication
from PySide2 import QtWidgets, QtCore, QtGui
from numpy.core.fromnumeric import repeat
from numpy.core.memmap import memmap
# app = QApplication() 

#In[0]
from enum import auto

from qspreadsheet import *
from datetime import datetime, timedelta, time as dtime
import time
from typing import Any, DefaultDict, Dict
import numpy as np
from numpy.core.defchararray import center 
import pandas as pd
import string
import random
import collections
from IPython.display import display
pd.options.display.max_rows = 10
pd.options.display.max_columns = 15
pd.options.display.float_format = '{:,.2f}'.format

def rnd_txt(num_letters): return "".join(
    [random.choice(string.ascii_letters[:26]) for i in range(num_letters)])

def mock_df():
    area = pd.Series({0: 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
    population = pd.Series(
        {0: 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
    population = population.astype(float)
    # states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
    states = ['California', 'Texas', 'Texas', 'Texas', 'Illinois']
    df = pd.DataFrame({'states': states,
                       'area': area, 'population': population}, index=range(len(states)))
    dates = [pd.to_datetime('06-15-2020') + pd.DateOffset(i)
             for i in range(1, df.shape[0] + 1)]
    df['dates'] = dates
    df['bools'] = (df.index % 2 == 1)
    df['multip'] = df.population * 3.42 * df['bools']
    df['div'] = df.population / 2.3 * (~df['bools'])
    df['multip'] = (df['multip'] + df['div']).astype('float64')
    df['div'] = df['div'].astype('int32')
    # df.iloc[1, 0] = pd.NA
    # df.iloc[4, 4] = pd.NA
    # df.iloc[2, 0] = pd.NA
    # df.iloc[2, 1] = pd.NA
    df.iloc[1, 3] = pd.NaT
    df.iloc[2, 6] = pd.NA
    return df
df = mock_df()
df
#In[0]
unq_list = df['states'].drop_duplicates()
unq_list.sort_values()
# %%
for ndx, val in unq_list.items():
    print(ndx, val)
#In[0]
num_rows = 10000
df = pd.DataFrame(np.random.randn(num_rows,20))
rand_lines = [rnd_txt(3) for i in range(num_rows)]
df['B'] = rand_lines
df['C'] = pd.Timestamp('20130101')
df
#In[0]
df['B'].nunique(), df['B'].size
#In[0]
df.to_pickle('.ignore/data/10000rows.pkl')
#In[0]
pd.read_pickle('.ignore/data/10000rows.pkl')

#In[0]
sys.float_info