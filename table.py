import sys, os
import typing

import numpy as np 
import pandas as pd 

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

    def __init__(self, data: pd.DataFrame, header_model: CustomHeaderView, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self._data = data.copy()
        self._header_model = header_model
        self._header_model.filter_btn_mapper.mapped[str].connect(self.filter_clicked)
        self.filter_values_mapper = QSignalMapper(self)        
        self.logical = None
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
                return self._header_model.headers[section]
            if orientation == Qt.Vertical:
                return str(self._data.index[section])

        return None


    def on_horizontal_scroll(self, dx: int):
        self._header_model.fix_item_positions()


    def on_vertical_scroll(self, dy: int):
        pass


    def on_action_all_triggered(self, dx: int):
        self.logical


    def filter_clicked(self, name):
        print(name)