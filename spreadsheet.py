from custom_headers_abc_model import mock_df
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

from header import HeaderItem, ColumnHeaderWidget, CustomHeaderView


class DataFrameTableModel(QAbstractTableModel):

    def __init__(self, data: pd.DataFrame, header_model: CustomHeaderView, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self._data = data.copy()
        self.header_model = header_model
        for i, name in enumerate(self._data.columns):
            self.setHeaderData(i, Qt.Orientation.Horizontal, name, Qt.DisplayRole)


    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: typing.Any, role: int) -> bool:
        
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            self.header_model.create_header_item(value)
        elif orientation == Qt.Vertical:
            super().setHeaderData(section, orientation, value, role)

        return True


    def rowCount(self, parent: QModelIndex) -> int:
        return self._data.index.size


    def columnCount(self, parent: QModelIndex) -> int:
        return self._data.columns.size


    def data(self, index: QModelIndex, role: int) -> typing.Any:
        if role == Qt.DisplayRole:
            return float(self._data.iloc[index.row(), index.column()])

        return None


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)


    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self._data.shape[0]:

            self._data.iloc[index.row(), index.column()] = float(value)
            self.dirty = True

            self.dataChanged.emit(index, index)
            return True
        return False


    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Any:
        if section < 0:
            print('section: {}'.format(section))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # if len(self.header_model.headers) -1 < section:
                #     self.header_model.create_header_item(self._data.columns[section])
                return self.header_model.headers[section]
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
            
        return None


class MainWindow(QMainWindow):

    def __init__(self, table):
        super().__init__()

        self.table = table
        self.setCentralWidget(self.table)
        self.setMinimumSize(QSize(600, 400))
        

if __name__ == "__main__":
    rng = np.random.RandomState(42)
    df = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['A', 'B', 'C', 'D'])

    app = QApplication(sys.argv)
    table = QTableView()
    
    header_model = CustomHeaderView()
    model = DataFrameTableModel(data=df, header_model=header_model)
    table.setHorizontalHeader(header_model)
    table.setModel(model)

    window = MainWindow(table)
    # table.setMinimumSize(600, 450)
    window.show()
    sys.exit(app.exec_())