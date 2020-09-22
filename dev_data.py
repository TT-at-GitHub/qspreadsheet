# dev_data.py
#In[0]
import os, sys
from datetime import datetime, timedelta, time as dtime
import time
import numpy as np 
import pandas as pd
import string
import random

def mock_df():
    area = pd.Series({0: 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
    population = pd.Series(
        {0: 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
    population = population.astype(float)
    states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
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
    # df.iloc[1, 0] = np.nan
    # df.iloc[2, 0] = np.nan
    # df.iloc[2, 1] = np.nan
    # df.iloc[1, 3] = np.nan
    return df
df = mock_df()
df
#In[0]

import random
import time

DATE_FORMAT = r'%m/%d/%Y %I:%M %p'

def str_time_prop(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def random_date(start, end, prop):
    return str_time_prop(start, end, DATE_FORMAT, prop)

rnd_strdate = random_date("1/1/2015 1:30 PM", "12/31/2020 4:50 AM", random.random())
print(datetime.strptime(rnd_strdate, DATE_FORMAT))

#In[0]

def rnd_txt(): return "".join(
    [random.choice(string.ascii_letters[:26]) for i in range(15)])

def add_nulls(data, j):
    if j < 6:
        data[j][j] = np.nan
    if 5 < j < 11:
        ndx = j % 6
        data[j][ndx] = np.nan
        data[j][ndx + 1] = np.nan
    if j == 11:
        data[j] = [np.nan] * 5    

data = []
for j in range(10000):
    r = []
    for k in range(2):
        r.append(rnd_txt())
        
    r.append(random.randint(1, 20))
    r.append(random.random()*10)

    rnd_strdate = random_date("1/1/2015 1:30 PM", "12/31/2020 4:50 AM", random.random())
    r.append(datetime.strptime(rnd_strdate, DATE_FORMAT))
    
    r.append(rnd_txt())

    data.append(r)
    add_nulls(data, j)

df = pd.DataFrame(
    data, columns=['AAA', 'CCC', 'INT', 'FLOAT', 'DATETIME', 'DDD'])
df.head(n=15)
#In[0]
df.to_pickle('./.ignore/data/df-nulls.pkl')
#In[0]
pd.options.display.max_rows = 10
pd.options.display.max_columns = 15
pd.options.display.float_format = '{:,.2f}'.format
#In[0]
np.iinfo(np.intp).max
#In[0]
np.iinfo(np.intp).min