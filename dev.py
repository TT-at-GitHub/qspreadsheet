#In[0]
import sys, os
from PyQt5.QtCore import center
import numpy as np
import numpy
import pandas as pd 
import PySide2
plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

#In[0]
area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
df = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
df.area = df.area.astype(float)
df.iloc[0, 1] = 'c'
df.iloc[3, 1] = 'a'
s = df['area']
s

#In[0]
def sort_mix_values(s: pd.Series, na_position='last'):
    numeric = pd.to_numeric(s, errors='coerce')
    nnulls = numeric.isnull().sum()
    if nnulls:
        s = s.loc[numeric.sort_values(na_position='first').index]
        s[:nnulls] = s.iloc[:nnulls].sort_values()
    else:
        s.sort_values(na_position=na_position)
s
#In[0]
s[:nnulls] = s.iloc[:nnulls].sort_values()
s
#In[0]

# %%
df['typ'] = df['area'].apply(lambda x: type(x))
sort_ndx = (df.typ == str).sort_values(ascending=False).index
sort_ndx
#In[0]
df['area'].loc[sort_ndx]
#In[0]
