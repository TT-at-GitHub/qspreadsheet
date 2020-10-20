import sys, os

import numpy as np
import pandas as pd 

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

from fx import fx
from qspreadsheet import DataFrameView, automap_delegates, IntDelegate
from qspreadsheet import resources_rc

import logging
logging.basicConfig(level=logging.DEBUG)


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

# df = mock_df()
df = pd.read_pickle('.ignore/data/100_000rows.pkl')

# print(df)

pd.options.display.precision = 4

delegates = automap_delegates(df, nullable=True)
# delegates['div'] = IntDelegate().to_nullable()
# bools = delegates['bools'].to_non_nullable()
# delegates['bools'] = bools

table_view = DataFrameView(df=df, delegates=delegates)
table_view.set_columns_edit_state(df.columns.tolist(), True)
# table_view.set_columns_edit_state('div', False)
table_view.set_columns_edit_state('C', False)


window = MainWindow(table_view=table_view)

window.show()
sys.exit(app.exec_())
