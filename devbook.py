# dev_data.py
#In[0]
import os, sys
from datetime import datetime, timedelta, time as dtime
import time
import numpy as np
from numpy.core.defchararray import center 
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
    df.iloc[1, 0] = pd.NA
    df.iloc[4, 4] = pd.NA
    df.iloc[2, 0] = pd.NA
    df.iloc[2, 1] = pd.NA
    df.iloc[1, 3] = pd.NaT
    df.iloc[2, 6] = pd.NA
    return df
df = mock_df()
from IPython.display import display
display(df)
df.dtypes
#In[0]
s = df['div']
[type(v) for v in s]
s.isna().any()
#In[0]
df['dates'].iloc[2]
#In[0]
df.iat[2, 5]
#In[0]

df.iloc[2, 5] = 8543968.09765
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
df = df.append(pd.Series(np.nan, index=df.columns, name=df.index.size))
df
#In[0]
df = pd.DataFrame(index=np.arange(df.index.size), 
            columns=('InProgress', 'Foreground', 'Background'), 
            data=None)
df['InProgress'] = False
df
#In[0]
np.arange(df.index.size)
#In[0]
edit_columns = pd.Series(index=df.columns, data=True)
edit_columns
#In[0]
edit_columns.loc[['states', 'area']]
#In[0]
df = df.append(pd.Series(np.nan, index=df.columns, name=df.index.size))
df
#In[0]
row = 0
count = 1
rows_in_progress = pd.Series(
            index=df.index, data=False)
rows_in_progress
row, count
#In[0]
new_rows = pd.DataFrame(data=np.nan, columns=df.columns, 
    index=range(row, row + count))
new_rows
#In[0]
df_up = df.iloc[0 : row]
df_down = df.iloc[row :]
df_down.index = df_down.index + 1
#In[0]
dfr = pd.concat([df_up, new_rows, df_down])
dfr
#In[0]
df = df.append(new_rows)
rows_in_progress = rows_in_progress.append(
    pd.Series(data=False, index=new_rows.index))
df
#In[0]
rows_in_progress.iloc[row : row + count] = True
rows_in_progress
#In[0]
df = df.drop(index=df.index[[1, 2, 3]])
df
#In[0]
df.reset_index(drop=True)
#In[0]
rows = sorted([5, 2, 7, 8, 1, 3])
rows
#In[0]
from itertools import groupby, count

data = rows
print(data)

groups = []
for _, g in groupby(data, lambda n, c=count(): n-next(c)):
    groups.append(list(g))
groups