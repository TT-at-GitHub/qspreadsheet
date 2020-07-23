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
from table import DataFrameTableModel, DataFrameItemDelegate


class MainWindow(QMainWindow):

    def __init__(self, df: pd.DataFrame):
        super().__init__()

        table = QTableView()
        header_model = CustomHeaderView(columns=df.columns.tolist())
        model = DataFrameTableModel(data=df, header_model=header_model, parent=table)

        table.setHorizontalHeader(header_model)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().resizeSections(QHeaderView.Stretch)
        table.horizontalScrollBar().valueChanged.connect(model.on_horizontal_scroll)
        table.horizontalScrollBar().valueChanged.connect(model.on_vertical_scroll)
        table.setModel(model)

        item_delegete = DataFrameItemDelegate()
        table.setItemDelegate(item_delegete)
        
        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)
        layout.addWidget(table)
       
        self.table = table
        self.header_model = header_model
        self.model = model        

        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle("Table View")


    def filter_clicked(self, name):
        print(self.__class__.__name__, ': ', name)
        ndx = self._data.columns.get_loc(name)
        self.logical = self.logicalIndex(ndx)

        self.filter_menu = QMenu(self)
        self.filter_values_mapper
        unique_values = self._data[name].unique()

        action_all = QAction('All', self)
        action_all.triggered.connect(self.on_action_all_triggered)
        self.filter_menu.addAction(action_all)
        self.filter_menu.addSeparator()

        for i, name in enumerate(sorted(unique_values)):
            action = QAction(name, self)
            self.filter_values_mapper.setMapping(action, i)
            action.triggered.connect(self.filter_values_mapper.map)
            self.filter_menu.addAction(action)


if __name__ == "__main__":

    rng = np.random.RandomState(42)
    df = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['Abcd', 'Some very long header Background', 'Cell', 'Date'])

    app = QApplication(sys.argv)
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec_())