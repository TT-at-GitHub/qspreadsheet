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

#In[0]
num_rows = 1_000
df = pd.DataFrame(np.random.randn(num_rows,3))
rand_lines = [rnd_txt(3) for i in range(num_rows)]
df['B'] = rand_lines
df['C'] = pd.Timestamp('20130101')
df['C'] = df['C'].apply(lambda x: x + timedelta(days=randint(-30000, 30000)))
df.columns = df.columns.astype(str)
#In[0]
df['B'].nunique(), df['B'].size
#In[0]
df.to_pickle('.ignore/data/1_000rows.pkl')
#In[0]
df = pd.read_pickle('.ignore/data/1_000rows.pkl')
df = pd.DataFrame(df)
df.columns
#In[0]
