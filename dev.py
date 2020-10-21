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
        self.load_window_settings()
        self.setWindowTitle("Table View")

    def closeEvent(self, event: QCloseEvent):
        self.save_window_settings()
        event.accept()

    def save_window_settings(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 
                             'TT', 'qspreadsheet')
        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
        settings.endGroup()

    def load_window_settings(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 
                             'TT', 'qspreadsheet')
        settings.beginGroup('MainWindow')
        self.resize(QSize(settings.value('size', QSize(960, 640))))
        self.move(QPoint(settings.value('pos', QPoint(200, 200))))
        settings.endGroup()

app = QApplication(sys.argv)

# df = mock_df()
df = pd.DataFrame(pd.read_pickle('.ignore/data/10_000rows.pkl'))
df = df.sort_values(by='C').reset_index(drop=True)
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
