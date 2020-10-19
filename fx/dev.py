#In[0]
import sys, os
import numpy as np 
import pandas as pd 

from fx import fx

# %%
#In[0]
area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
df = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
df.area = df.area.astype(float)
df.iloc[0, 1] = 'c'
df.iloc[2, 1] = np.nan
df.iloc[3, 1] = 'a'
s = df['area']
s
#In[0]
fx.sort_mix_values(s)

# %%
