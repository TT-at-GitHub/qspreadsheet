import sys, os
import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt

import numpy as np
import pandas as pd


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data


    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]


    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)


    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, data):
        super().__init__()

        self.table = QtWidgets.QTableView()


        self.model = TableModel(data)
        self.table.setModel(self.model)

        self.setCentralWidget(self.table)


rng = np.random.RandomState(42)
data = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['A', 'B', 'C', 'D'])

app=QtWidgets.QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()