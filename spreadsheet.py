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


    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        print(source_row)
        return True


    def setCustomFilter(self, name: str):
        print(f'Filter column: {name}')
        self.invalidateFilter()



class DataFrameView(QTableView):

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)
        
        self.header_model = CustomHeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self.header_model)

        self.model = DataFrameModel(df=df, header_model=self.header_model, parent=self)
        self.header_model.filter_btn_mapper.mapped[str].connect(self.filter_clicked)

        self.proxy = DataFrameSortFilterProxy()
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self.model.on_horizontal_scroll)
        self.horizontalScrollBar().valueChanged.connect(self.model.on_vertical_scroll)

        delegate = DataFrameDelegate(self)
        self.setItemDelegate(delegate)

        # Create header menu bindings
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self._header_menu)
        

    @property
    def df(self):
        return self.model.df

    @df.setter
    def df(self, df: pd.DataFrame):
        # Use the "hard setting" of the dataframe because anyone who's interacting with the
        #  DataFrameWidget (ie, end user) would be setting this
        self.model.df(df)

    def filter_clicked(self, name):
        self.proxy.setCustomFilter(name)


class MainWindow(QMainWindow):

    def __init__(self, df: pd.DataFrame):
        super().__init__()

        self.table = DataFrameView(df, self)
        self.setCentralWidget(self.table)
        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle("Table View")


def mock_df():
    area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
    pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
    states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
    df = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
    return df


if __name__ == "__main__":

    app = QApplication(sys.argv)

    df = mock_df()
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec_())