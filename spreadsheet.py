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

    def __init__(self, table):
        super().__init__()

        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)
        layout.addWidget(table)
        
        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle("Table View")
        

if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    rng = np.random.RandomState(42)
    df = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['Abcd', 'Some very long header Background', 'Cell', 'Date'])

    header_model = CustomHeaderView(columns=df.columns.tolist())
    model = DataFrameTableModel(data=df, headers=header_model.headers)

    table = QTableView()
    table.setHorizontalHeader(header_model)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setMinimumSectionSize(100)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.horizontalHeader().resizeSections(QHeaderView.Stretch)
    table.setModel(model)

    item_delegete = DataFrameItemDelegate()
    table.setItemDelegate(item_delegete)

    window = MainWindow(table)
    table.setMinimumSize(600, 450)
    window.show()
    sys.exit(app.exec_())