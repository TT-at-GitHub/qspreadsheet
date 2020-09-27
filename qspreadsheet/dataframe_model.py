import logging
import sys
import os
from typing import Any, List, Optional

import numpy as np
from numpy.core.defchararray import index
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
        self.add_bottom_row()

        self.rows_in_progress = pd.Series(data=False, index=self.df.index)
        self.accepted_mask = pd.Series(data=True, index=self.df.index)

        self.editable_columns = pd.Series(index=df.columns, data=True)
        self.delegate = delegate

        self.header_model = header_model
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self.filter_values_mapper = QSignalMapper(self)

        self.rows_mutable = True
        self.is_dirty = False

    def rowCount(self, parent: QModelIndex) -> int:
        return self.df.shape[0]

    def columnCount(self, parent: QModelIndex) -> int:
        return self.df.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:

        if role == Qt.DisplayRole:
            if index.row() == self.rowCount(index) - 1:
                return ''
            return self.delegate.display_data(index,
                                              self.df.iloc[index.row(), index.column()])

        if role == Qt.EditRole:
            if index.row() == self.rowCount(index) - 1:
                return self.delegate.default(index)
            # if self.rows_in_progress.loc[index.row()]:
            #     return self.delegate.default(index)
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

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        if not index.isValid():
            return False

        if index.row() == self.rowCount(index) - 1:
            self.insertRow(index.row(), index)

        self.df.iloc[index.row(), index.column()] = value

        self.is_dirty = True
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if section < 0:
            print('section: {}'.format(section))

        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if section == self.rowCount(index) - 1:
                    return '*'
                return str(self.df.index[section])
            if role == Qt.ForegroundRole:
                if self.rows_in_progress.loc[section]:
                    return QColor(255, 0, 0)
                return None
            return None
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.header_model.headers[section]
            return None
        return None

    def insertRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        self.beginInsertRows(QModelIndex(), row, row + count - 1)


        df_above = self.df.iloc[0: row]
        new_rows = pd.DataFrame(data=np.nan, columns=self.df.columns,
                                index=range(row, row + count))
        df_below = self.df.iloc[row:]
        df_below.index = df_below.index + count
        self.df = pd.concat([df_above, new_rows, df_below])

        self.rows_in_progress = self.insert_util_rows(
            self.rows_in_progress ,row, count, new_rows, True)

        self.accepted_mask = self.insert_util_rows(
            self.accepted_mask ,row, count, new_rows, True)

        self.endInsertRows()
        return True

    def insert_util_rows(self, obj, row: int, count: int, new_rows_df: DF, value: Any):
        above = obj.iloc[0: row]
        new_rows = pd.Series(value, new_rows_df.index)
        below = obj.iloc[row:]
        below.index = below.index + count
        obj = pd.concat([
            above, new_rows, below])
        return obj

    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        logger.debug('removeRows(first:{}, last:{}), num rows: {}'.format(
            row, row + count - 1, count))
        self.beginRemoveRows(index, row, row + count - 1)

        self.endRemoveRows()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = QAbstractTableModel.flags(self, index)

        if self.rows_mutable:
            if index.row() == self.rowCount(index) - 1:
                flag |= Qt.ItemIsEditable
            elif self.rows_in_progress.loc[index.row()]:
                flag |= Qt.ItemIsEditable

        if self.editable_columns.iloc[index.column()]:
            flag |= Qt.ItemIsEditable
        return flag

    def on_horizontal_scroll(self, dx: int):
        self.header_model.fix_item_positions()

    def on_vertical_scroll(self, dy: int):
        pass

    def filter_clicked(self, name):
        pass

    def enable_mutable_rows(self, enable: bool):
        self.rows_mutable = enable

    def add_bottom_row(self):
        bottom_row = pd.Series(
            np.nan, index=self.df.columns, name=self.df.index.size)
        self.df = self.df.append(bottom_row)
