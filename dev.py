#In[0]
import sys, os
from PyQt5.QtCore import center
import numpy as np
import numpy
import pandas as pd 



from fx import fx

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
s = fx.to_mixed_intstr(s)
s.unique()
#In[0]
fx.sort_mix_values(pd.Series(data=list(s.unique())))

#In[0]
set(s.astype(str))
#In[0]

import string
import random

rnd_txt = lambda: "".join( [random.choice(string.ascii_letters[:26]) for i in range(15)] )
data = []
for j in range(5):
    r = []
    for k in range(6):
        r.append(rnd_txt())
    r.append(random.randint(1,20))
    r.append(random.random()*10)
    data.append(r)
df = pd.DataFrame(data, columns=['AAA','BBB','CCC','DDD','EEE','FFF','GGG','HHH'])

#In[0]
help(pd.Series.sort_values)