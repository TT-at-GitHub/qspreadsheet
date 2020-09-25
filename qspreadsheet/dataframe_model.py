import logging
import sys
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.common import DF, SER
from qspreadsheet.delegates import ColumnDelegate
from qspreadsheet.header_view import HeaderView
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: DF, header_model: HeaderView,
                 delegate: ColumnDelegate, parent: Optional[QWidget] = None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.df = df.copy()
        self.editable_column_indices: List[int] = []
        self._header_model = header_model
        self._header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)
        self.delegate = delegate

        self.filter_values_mapper = QSignalMapper(self)
        self.new_row: Optional[SER] = None
        self.new_row_in_progress = False
        self.is_dirty = False

    def rowCount(self, parent: QModelIndex) -> int:
        return self.df.shape[0] + 1

    def columnCount(self, parent: QModelIndex) -> int:
        return self.df.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if index.row() == self.df.shape[0]:
            return None
        
        if role == Qt.DisplayRole:
            return self.delegate.display_data(index, 
                self.df.iloc[index.row(), index.column()])
        if role == Qt.EditRole:
            return self.df.iloc[index.row(), index.column()]
        if role == Qt.TextAlignmentRole:
            return int(self.delegate.alignment(index))
        if role == Qt.BackgroundRole:
            if self.flags(index) & Qt.ItemIsEditable:
                return self.delegate.background_brush(index)
            return QApplication.palette().alternateBase()
        if role == Qt.ForegroundRole:
            return self.delegate.foreground_brush(index)
        if role == Qt.FontRole:
            return self.delegate.font(index)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = QAbstractTableModel.flags(self, index)
        if index.column() in self.editable_column_indices:
            flag |= Qt.ItemIsEditable
        return flag

    def insertRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        self.beginInsertRows(parent, row, row + count - 1)
        
        if not self.new_rows is None:
            pass

        self.endInsertRows()
        return True
        
    def new_row_setData(self, index: QModelIndex, value: Any):
        if self.new_row_in_progress:
            self.new_row.iloc[index.column()] = value
        else:
            self.new_row_in_progress
            self.new_row = pd.Series(index=self.df.columns)
        self.new_row.iloc[index.column()] = value
        
    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole):
        if not index.isValid():
            return False

        if index.row() == self.df.shape[0]:
            self.update_new_row(index, value)

        self.df.iloc[index.row(), index.column()] = value
        self.is_dirty = True
        self.dataChanged.emit(index, index)
        return True

    def new_row_headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if role == Qt.DisplayRole:
            return '*'

        if role == Qt.ForegroundRole:
            return None
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if section < 0:
            print('section: {}'.format(section))

        if orientation == Qt.Vertical:
            if section == self.df.shape[0]:
                return self.new_row_headerData(section, orientation, role)
            if role == Qt.DisplayRole:
                return str(self.df.index[section])

        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._header_model.headers[section]
        return None

    def on_horizontal_scroll(self, dx: int):
        self._header_model.fix_item_positions()

    def on_vertical_scroll(self, dy: int):
        pass

    def filter_clicked(self, name):
        pass
