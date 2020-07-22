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

from header import CustomHeaderView



class DataFrameItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(DataFrameItemDelegate, self).__init__(parent)


    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)


    def sizeHint(self, option, index):
        return QStyledItemDelegate.sizeHint(self, option, index)


    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            background-color:#fffd99
        """)
        editor.returnPressed.connect(self.commitAndCloseEditor)
        return editor
        # else:
        #     return QStyledItemDelegate.createEditor(self, parent, option, index)


    def commitAndCloseEditor(self):
        editor = self.sender()
        # if isinstance(editor, (QTextEdit, QLineEdit)):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole)
        editor.setText(text)
        # else:
            # QStyledItemDelegate.setEditorData(self, editor, index)


    def setModelData(self, editor, model, index):
        QStyledItemDelegate.setModelData(self, editor, model, index)



class DataFrameTableModel(QAbstractTableModel):

    def __init__(self, data: pd.DataFrame, headers: list, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self._data = data.copy()
        self._headers = headers
        self.dirty = False


    def rowCount(self, parent: QModelIndex) -> int:
        return self._data.index.size


    def columnCount(self, parent: QModelIndex) -> int:
        return self._data.columns.size


    def data(self, index: QModelIndex, role: int) -> typing.Any:
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])

        return None


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)


    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self._data.shape[0]:
            if not value:
                self._data.iloc[index.row(), index.column()] = np.nan
            else:
                try:
                    number = pd.to_numeric(value)
                except :
                    self._data.iloc[index.row(), index.column()] = str(value)
                else:
                    self._data.iloc[index.row(), index.column()] = number

            self.dirty = True

            self.dataChanged.emit(index, index)
            return True
        return False


    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Any:
        if section < 0:
            print('section: {}'.format(section))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            if orientation == Qt.Vertical:
                return str(self._data.index[section])

        return None


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