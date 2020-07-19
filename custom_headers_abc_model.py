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

class MyTableModel(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame, header_model: QHeaderView, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.df = df
        self.header_model = header_model

    def rowCount(self, parent: QModelIndex) -> int:
        return self.df.index.size

    def columnCount(self, parent: QModelIndex) -> int:
        return self.df.columns.size

    def data(self, index: QModelIndex, role: int) -> typing.Any:
        if role == Qt.DisplayRole:
            
            val = df.iat[index.row(), index.column()]
            print((index.row(), index.column()), ':', val, type(val))
            return int(val)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Any:

        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section >= 0:

            if len(self.header_model.headers) -1 < section:
                header = HeaderItem(widget=ColumnHeaderWidget(labelText=self.df.columns[section]))
                self.header_model.headers.append(header)
            return self.header_model.headers[section]

        return None


def mock_df():
    rng = np.random.RandomState(42)
    data = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['A', 'B', 'C', 'D'])
    return data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    table = QTableView()
    header_model = CustomHeaderView()
    df = mock_df()
    print(df)
    model = MyTableModel(df=df, header_model=header_model)
    table.setModel(model)
    table.setHorizontalHeader(header_model)
    table.setMinimumSize(600, 450)
    table.show()
    sys.exit(app.exec_())