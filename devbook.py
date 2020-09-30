# dev_data.py
#In[0]
from enum import auto
import os, sys
from qspreadsheet.delegates import MasterDelegate
from qspreadsheet import automap_delegates, DF, SER
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
    # df.iloc[4, 4] = pd.NA
    df.iloc[2, 0] = pd.NA
    df.iloc[2, 1] = pd.NA
    df.iloc[1, 3] = pd.NaT
    df.iloc[2, 6] = pd.NA
    return df
df = mock_df()
df
# df.to_pickle('./.ignore/data/df-nulls.pkl')
# df.head(n=15)
#In[0]
def null_rows(df, delegate, start_index: int, count: int) -> DF:
    nulls_row: Dict[int, Any] = delegate.null_value()
    data = {df.columns[ndx]: null_value
            for ndx, null_value in nulls_row.items()}

    nulls_df = pd.DataFrame(data=data,
                            index=range(start_index, start_index + count))
    return nulls_df

delegates = automap_delegates(df)
delegate = MasterDelegate()
for column, column_delegate in delegates.items():
    icolumn = df.columns.get_loc(column)
    delegate.add_column_delegate(icolumn, column_delegate)

editable_columns = pd.Series(index=df.columns, data=True)
nullable_columns_indices = delegate.nullable_delegates.keys()
display(editable_columns)
display(nullable_columns_indices)
#In[0]
row = 0
count = 1
rows_in_progress = pd.Series(
            index=df.index, data=False)
display(rows_in_progress)
row, count
#In[0]
new_rows = null_rows(df, delegate, row, count)
df_up = df.iloc[0 : row]
df_down = df.iloc[row :]
df_down.index = df_down.index + 1
df = pd.concat([df_up, new_rows, df_down])
df
rows_in_progress = pd.Series(data=False, index=df.index)
rows_in_progress.loc[new_rows.index] = True
display(df)
display(rows_in_progress)
#In[0]
# Get data changed loc from first/second index

# For all non editable columns, any null values in data changed,
# gain 'row in progress' status

# For all non nullable columns with null values in data changed,
# gain 'row in progress' status

# Find intersection between the data changed and the rows in progress.


# All progress rows in data changed, with all non-null values or with null
# values only in nullable columns, loose the 'row in progress' status