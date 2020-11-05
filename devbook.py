#In[0]
import os, sys
from random import randint
import random
import string
from PySide2.QtWidgets import QApplication
from PySide2 import QtWidgets, QtCore, QtGui
from numpy.core.fromnumeric import repeat
from numpy.core.memmap import memmap

from enum import auto

from pandas._libs.tslibs import Timestamp
from pandas.core.indexes.api import union_indexes
from six import Iterator

from qspreadsheet import *
from datetime import datetime, timedelta, time as dtime
import time
from typing import Any, DefaultDict, Dict
import numpy as np
from numpy.core.defchararray import center, upper 
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

#In[0]
num_rows = 10
df = pd.DataFrame(np.random.randn(num_rows,3))
rand_lines = [rnd_txt(3) for i in range(num_rows)]
df['B'] = rand_lines
df['C'] = pd.Timestamp('20130101')
df['C'] = df['C'].apply(lambda x: x + timedelta(days=randint(-30000, 30000)))
df.columns = df.columns.astype(str)
#In[0]
half_sz = int(df.index.size / 2)
df
#In[0]
df.B[1:half_sz:2] = df.B[:half_sz -1 : 2].apply(str.upper)
df
#In[0]
df.B[half_sz :-1:2] = df.B[half_sz + 1::2].apply(str.upper)
df
#In[0]
df.C[:] = df.C.sort_values()
df
#In[0]
df.to_pickle('.ignore/data/{}rows.pkl'.format(num_rows))
#In[0]
df.to_excel('.ignore/data/{}rows.xlsx'.format(num_rows))
#In[0]
df = pd.read_pickle('.ignore/data/{}rows.pkl'.format(num_rows))
df = pd.DataFrame(df)
df
#In[0]
unique = df.B.drop_duplicates()
unique.name
INITIAL_FILTER_LIMIT = 5000
STEP = 1000
#In[0]
display_values_gen = ((ndx, value) for ndx, value in unique.items())
display_values_gen
display_values = pd.Series(name=unique.name)
#In[0]
if unique.size > INITIAL_FILTER_LIMIT:
    print('unique.size {} > INITIAL_FILTER_LIMIT {}'.format(unique.size , INITIAL_FILTER_LIMIT))
next_step = INITIAL_FILTER_LIMIT
remaining = unique.size
print('next_n {}, remaining {}'.format(next_step, remaining))
#In[0]
while next_step and display_values.size < INITIAL_FILTER_LIMIT:
    print('next_n {}, remaining {}'.format(next_step, remaining))
    x = pd.Series(dict(next(display_values_gen) 
                    for _ in range(next_step)))
    display_values = display_values.append(x)
    print(display_values)
    unique_index = display_values.str.lower().drop_duplicates().index
    display_values = display_values.loc[unique_index]
    print(display_values)
    remaining -= next_step
    next_step = max(min(STEP, remaining), 0)
'display_values.size', display_values.size, 'remaining', remaining
# %%
df.B