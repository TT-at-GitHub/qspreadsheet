import logging
import sys
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.common import DF, SER, pandas_obj_insert_rows, pandas_obj_remove_rows
from qspreadsheet.delegates import MasterDelegate
from qspreadsheet.header_view import HeaderView
from qspreadsheet._ndx import _Ndx
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: DF, header_model: HeaderView,
                 delegate: MasterDelegate, parent: Optional[QWidget] = None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.delegate = delegate
        self.set_df(df)

        non_nullables = list(self.delegate.non_nullable_delegates.keys())
        self.col_ndx.non_nullable_mask.iloc[non_nullables] = True

        self.header_model = header_model
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self.is_dirty = False

        self.dataChanged.connect(self.on_dataChanged)
        self.rowsInserted.connect(self.on_rowsInserted)
        self.rowsRemoved.connect(self.on_rowsRemoved)

    def set_df(self, df: DF):
        # self.beginResetModel()
        self._df = df.copy()
        self.row_ndx = _Ndx(self._df.index)
        self.col_ndx = _Ndx(self._df.columns)
        self.add_bottom_row()
        # self.endResetModel()

    @property
    def df(self):
        df = self._df
        not_inprogress_rows = ~self.row_ndx.in_progress_mask
        # TODO: FIXME: self.col_ndx.in_progress_mask.values
        # NOTE: converting to 'values' array is needed because
        # the column index is not numeric, so it maybe be better
        # to make the row and column index datatype agnostic
        not_inprogress_columns = ~self.col_ndx.in_progress_mask.values
        df.loc[not_inprogress_rows, not_inprogress_columns]
        df = df.iloc[ : self.row_ndx.count_real]
        return df

    def columnCount(self, parent: QModelIndex) -> int:
        return self.col_ndx.size

    def rowCount(self, parent: QModelIndex) -> int:
        return self.row_ndx.size

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        # logger.debug('data({}, {}), role: {}'.format( index.row(), index.column(), role))
        if index.row() < 0:
            logger.error('index.row() < 0')
            return None

        value = self._df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if index.row() == self.row_ndx.count_real:
                return ''
            return self.delegate.display_data(index, value)

        if role == Qt.EditRole:
            if index.row() == self.row_ndx.count_real:
                return self.delegate.default_value(index)
            return value

        if role == Qt.TextAlignmentRole:
            return int(self.delegate.alignment(index))

        if role == Qt.BackgroundRole:
            if self.flags(index) & Qt.ItemIsEditable:
                return self.delegate.background_brush(index)
            return QApplication.palette().alternateBase()

        if role == Qt.ForegroundRole:
            if self.row_ndx.in_progress_mask.iloc[index.row()] \
                    and self.col_ndx.disabled_mask.iloc[index.column()]:
                return QColor(255, 0, 0)
            if self.row_ndx.in_progress_mask.iloc[index.row()] \
                    and self.col_ndx.non_nullable_mask.iloc[index.column()]:
                if pd.isnull(value):
                    return QColor(255, 0, 0)

            return self.delegate.foreground_brush(index)

        if role == Qt.FontRole:
            return self.delegate.font(index)

        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        if not index.isValid():
            return False

        # If user has typed in the last row
        if index.row() == self.row_ndx.count_real:
            self.insertRow(self.row_ndx.count_real, QModelIndex())

        self._df.iloc[index.row(), index.column()] = value

        # update rows in progress
        if self.row_ndx.in_progress_mask.iloc[index.row()]:
            if self.col_ndx.disabled_mask.iloc[index.column()]:
                self.row_ndx.reduce_disabled_in_progress(index.row())

            if self.col_ndx.non_nullable_mask.iloc[index.column()]:
                value = self._df.iloc[index.row(), index.column()]
                if not pd.isnull(value):
                    self.row_ndx.reduce_non_nullable_in_progress(index.row())

        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:

        if section < 0:
            logger.error('section: {}'.format(section))
            return None

        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if section == self.row_ndx.count_real:
                    return '*'
                return str(self._df.index[section])
            if role == Qt.ForegroundRole:
                if self.row_ndx.in_progress_mask.iloc[section]:
                    return QColor(255, 0, 0)
                return None
            return None
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.header_model.header_widgets[section]
            return None
        return None

    def insertRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        if self.row_ndx.is_mutable == False:
            logger.error('Calling `insertRows` on immutable row index.')
            return False

        self.beginInsertRows(QModelIndex(), row, row + count - 1)

        new_rows = self.null_rows(start_index=row, count=count)
        self._df = pandas_obj_insert_rows(self._df, row, new_rows)

        self.endInsertRows()
        self.dataChanged.emit(self.index(row, 0), self.index(
            row + count, self.col_ndx.size))
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        if self.row_ndx.is_mutable == False:
            logger.error('Calling `removeRows` on immutable row index.')
            return False

        # logger.debug('removeRows(first:{}, last:{}), num rows: {}'.format(
        #     row, row + count - 1, count))
        self.beginRemoveRows(parent, row, row + count - 1)
        self._df = pandas_obj_remove_rows(self._df, row, count)
        self.endRemoveRows()
        self.dataChanged.emit(self.index(
            row, 0), self.index(row, self.col_ndx.size))
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = QAbstractTableModel.flags(self, index)

        if self.row_ndx.is_mutable:
            if index.row() == self.row_ndx.count_real:
                flag |= Qt.ItemIsEditable
            elif self.row_ndx.in_progress_mask.iloc[index.row()]:
                flag |= Qt.ItemIsEditable

        if not self.col_ndx.disabled_mask.iloc[index.column()]:
            flag |= Qt.ItemIsEditable
        return flag

    def on_horizontal_scroll(self, dx: int):
        self.header_model.fix_item_positions()

    def on_vertical_scroll(self, dy: int):
        pass

    def filter_clicked(self, name):
        pass

    def enable_mutable_rows(self, enable: bool):
        if self.row_ndx.is_mutable == enable:
            return
        # FIXME: make this dynamic
        if enable:
            self.row_ndx.is_mutable = enable
            self.insertRow(self.row_ndx.count_real + 1, self.index(0, 0).parent())
        else:
            self.removeRow(self.row_ndx.count_real, QModelIndex())
            self.row_ndx.is_mutable = enable

    def add_bottom_row(self):
        at_index = self._df.index.size
        bottom_row = self.null_rows(start_index=at_index, count=1)
        self._df = self._df.append(bottom_row)
        self.row_ndx.insert(at_index, 1)

    def null_rows(self, start_index: int, count: int) -> DF:
        nulls_row: Dict[int, Any] = self.delegate.null_value()
        data = {self._df.columns[ndx]: null_value
                for ndx, null_value in nulls_row.items()}

        nulls_df = pd.DataFrame(data=data,
                                index=range(start_index, start_index + count))
        return nulls_df

    def on_dataChanged(self, first: QModelIndex, last: QModelIndex, roles):
        self.is_dirty = True

    def on_rowsInserted(self, parent: QModelIndex, first: int, last: int):
        self.is_dirty = True
        self.row_ndx.insert(at_index=first, count=last - first + 1)

        rows_inserted = list(range(first, last + 1))

        # If there are disabled columns, all inserted rows
        # gain 'row in progress' status
        if self.col_ndx.disabled_mask.any():
            self.row_ndx.set_disabled_in_progress(
                rows_inserted, self.col_ndx.disabled_mask.sum())

        if self.col_ndx.non_nullable_mask.any():
            self.row_ndx.set_non_nullable_in_progress(
                rows_inserted, self.col_ndx.non_nullable_mask.sum())

    def on_rowsRemoved(self, parent: QModelIndex, first: int, last: int):
        self.is_dirty = True
        self.row_ndx.remove(at_index=first, count=last - first + 1)
