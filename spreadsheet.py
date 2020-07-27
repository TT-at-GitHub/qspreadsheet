import sys, os
import typing

import numpy as np 
import pandas as pd 

import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from header import CustomHeaderView
from table import DataFrameModel, DataFrameDelegate


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self) -> None:
        super(DataFrameSortFilterProxy, self).__init__()


class DataFrameView(QTableView):

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)
        
        self.header_model = CustomHeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self.header_model)

        self.model = DataFrameModel(df=df, header_model=self.header_model, parent=self)
        self.proxy = DataFrameSortFilterProxy()
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self.model.on_horizontal_scroll)
        self.horizontalScrollBar().valueChanged.connect(self.model.on_vertical_scroll)

        delegate = DataFrameDelegate(self)
        self.setItemDelegate(delegate)

    @property
    def df(self):
        return self.model.df

    @df.setter
    def df(self, df: pd.DataFrame):
        # Use the "hard setting" of the dataframe because anyone who's interacting with the
        #  DataFrameWidget (ie, end user) would be setting this
        self.model.df(df)


class MainWindow(QMainWindow):

    def __init__(self, df: pd.DataFrame):
        super().__init__()

        self.table = DataFrameView(df, self)
        self.setCentralWidget(self.table)
        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle("Table View")


if __name__ == "__main__":

    rng = np.random.RandomState(42)
    df = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['Abcd', 'Some very long header Background', 'Cell', 'Date'])

    app = QApplication(sys.argv)
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec_())