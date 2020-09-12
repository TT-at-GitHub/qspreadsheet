#In[0]
import sys, os
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import numpy as np
import pandas as pd 
from datetime import datetime, timedelta
from fx import fx
from qspreadsheet import MainWindow


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
    df['multip'] = (df['multip'] + df['div']).astype('float32')
    df['div'] = df['div'].astype('int32')
    df.iloc[1, 0] = np.nan
    df.iloc[2, 0] = np.nan
    df.iloc[2, 1] = np.nan
    df.iloc[1, 3] = np.nan
    return df


app = QApplication(sys.argv)

df = mock_df()
window = MainWindow(df)
window.show()
sys.exit(app.exec_())