import logging
import sys
import os
from qspreadsheet.delegates import ColumnDelegate, GenericDelegate, automap_delegates
from functools import partial
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union
import logging

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.header import HeaderView
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame, header_model: HeaderView,
                 delegate: ColumnDelegate, parent: Optional[QWidget] = None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.df = df.copy()
        self.editable_column_indices: List[int] = []
        self._header_model = header_model
        self._header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)
        self.delegate = delegate

        self.filter_values_mapper = QSignalMapper(self)
        self.logical = None
        self.dirty = False

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

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        self.df.iloc[index.row(), index.column()] = value
        self.dirty = True
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if section < 0:
            print('section: {}'.format(section))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header_model.headers[section]
            if orientation == Qt.Vertical:
                if section == self.df.shape[0]:
                    return '*'
                return str(self.df.index[section])

        return None

    def on_horizontal_scroll(self, dx: int):
        self._header_model.fix_item_positions()

    def on_vertical_scroll(self, dy: int):
        pass

    def on_action_all_triggered(self, dx: int):
        self.logical

    def filter_clicked(self, name):
        pass
