from qspreadsheet.delegates import DateDelegate, IntDelegate, NullableColumnDelegate, automap_delegates
import sys, os
from typing import Optional

import numpy as np
import pandas as pd 

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *


from datetime import datetime, timedelta
from fx import fx
from qspreadsheet import DataFrameView, DataFrameModel, delegates


import logging
logging.basicConfig(level=logging.DEBUG)


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
    df.iloc[1, 0] = np.nan
    df.iloc[4, 4] = pd.NA
    df.iloc[2, 0] = np.nan
    df.iloc[2, 1] = np.nan
    df.iloc[1, 3] = pd.NaT
    df.iloc[2, 6] = np.nan
    return df


class MainWindow(QMainWindow):

    def __init__(self, table_view: DataFrameView):
        super(MainWindow, self).__init__()

        central_widget = QWidget(self)
        h_layout = QHBoxLayout()
        central_widget.setLayout(h_layout)
        h_layout.addWidget(table_view)

        self.setCentralWidget(central_widget)
        self.setMinimumSize(QSize(960, 640))
        self.setWindowTitle("Table View")

app = QApplication(sys.argv)

df = mock_df()
pd.options.display.precision = 4

delegates = automap_delegates(df)

nullable_delegates = {column : delegate.to_nullable() 
                      for column, delegate in delegates.items()}

table_view = DataFrameView(df=df, delegates=nullable_delegates)
window = MainWindow(table_view=table_view)

window.show()
sys.exit(app.exec_())
