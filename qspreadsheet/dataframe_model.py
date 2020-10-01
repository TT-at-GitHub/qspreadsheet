import logging
import sys
import os
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.common import DF, SER
from qspreadsheet.delegates import MasterDelegate
from qspreadsheet.header_view import HeaderView
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


def pandas_obj_insert_rows(obj: Union[DF, SER], at_index: int,
                            new_rows: Union[DF, SER]) -> Union[DF, SER]:
    above = obj.iloc[0: at_index]
    below = obj.iloc[at_index:]
    below.index = below.index + new_rows.index.size
    obj = pd.concat([above, new_rows, below])
    return obj


def pandas_obj_remove_rows(obj: Union[DF, SER], row: int, count: int) -> Union[DF, SER]:
    index_rows = range(row, row + count)
    obj = obj.drop(index=obj.index[index_rows])
    obj = obj.reset_index(drop=True)
    return obj


class _Ndx():
    def __init__(self, pd_ndx: pd.Index) -> None:
        self.pd_ndx = pd_ndx
        all_false = pd.Series(data=False, index=range(self.pd_ndx.size))
        self.disabled_mask: SER = all_false
        self.non_nullable_mask: SER = all_false
        self.in_progress_mask: SER = all_false
        self.filter_mask: SER = (~all_false)
        self.is_mutable = True

    def insert(self, at_index: int, count: int):
        # set new row as 'not in progress' by default
        new_rows = pd.Series(data=False, index=range(at_index, at_index + count))
        self.in_progress_mask = pandas_obj_insert_rows(
            obj=self.in_progress_mask, at_index=at_index, new_rows=new_rows)

        # set new at_index as 'not filtered' by default
        new_rows = pd.Series(data=True, index=range(at_index, at_index + count))
        self.filter_mask = pandas_obj_insert_rows(
            obj=self.filter_mask, at_index=at_index, new_rows=new_rows)

    def remove(self, at_index: int, count: int):
        self.in_progress_mask = pandas_obj_remove_rows(
            self.in_progress_mask, at_index, count)
        self.filter_mask = pandas_obj_remove_rows(
            self.filter_mask, at_index, count)


class DataFrameModel(QAbstractTableModel):
    
    def __init__(self, df: DF, header_model: HeaderView,
                 delegate: MasterDelegate, parent: Optional[QWidget] = None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.delegate = delegate
        self.df = df.copy()
        self.row_ndx = _Ndx(self.df.index)
        self.col_ndx = _Ndx(self.df.columns)
        self.add_bottom_row()

        non_nullables = list(self.delegate.non_nullable_delegates.keys())
        self.col_ndx.non_nullable_mask.iloc[non_nullables] = True

        self.header_model = header_model
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self.is_dirty = False
        
        self.dataChanged.connect(self.on_dataChanged)
        self.rowsInserted.connect(self.on_rowsInserted)
        self.rowsRemoved.connect(self.on_rowsRemoved)

    def progressRowCount(self) -> int:
        return self.row_ndx.in_progress_mask.sum()

    def dataRowCount(self) -> int:
        return self.df.shape[0] - self.rows_mutable

    def commitRowCount(self) -> int:
        return self.dataRowCount() - self.progressRowCount()

    def columnCount(self, parent: QModelIndex) -> int:
        return self.df.shape[1]

    def rowCount(self, parent: QModelIndex) -> int:
        return self.df.shape[0]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        # logger.debug('data({}, {}), role: {}'.format( index.row(), index.column(), role))
        if index.row() < 0:
            logger.error('index.row() < 0')
            return None

        if role == Qt.DisplayRole:
            if index.row() == self.dataRowCount():
                return ''
            return self.delegate.display_data(
                index, self.df.iloc[index.row(), index.column()])

        if role == Qt.EditRole:
            if index.row() == self.dataRowCount():
                return self.delegate.default_value(index)
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

        # If user has typed in the last row
        if index.row() == self.dataRowCount():
            self.add_bottom_row()

        old_value = self.df.iloc[index.row(), index.column()]
        self.df.iloc[index.row(), index.column()] = value

        if value != old_value:
            self.dataChanged.emit(index, index)

        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:

        if section < 0:
            logger.error('section: {}'.format(section))
            return None

        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if section == self.dataRowCount():
                    return '*'
                return str(self.df.index[section])
            if role == Qt.ForegroundRole:
                if self.row_ndx.in_progress_mask.loc[section]:
                    return QColor(255, 0, 0)
                return None
            return None
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.header_model.headers[section]
            return None
        return None

    def insertRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        if self.row_ndx.is_mutable == False:
            logger.error('Calling `insertRows` for immutable row index.')
            return False

        self.beginInsertRows(QModelIndex(), row, row + count - 1)

        new_rows = self.null_rows(start_index=row, count=count)
        self.df = pandas_obj_insert_rows(self.df, row, new_rows)
        self.row_ndx.insert(row, count)
        self.endInsertRows()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:
        if self.row_ndx.is_mutable == False:
            logger.error('Calling `removeRows` for immutable row index.')
            return False

        logger.debug('removeRows(first:{}, last:{}), num rows: {}'.format(
            row, row + count - 1, count))
        self.beginRemoveRows(parent, row, row + count - 1)
        self.df = pandas_obj_remove_rows(self.df, row, count)
        self.endRemoveRows()
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = QAbstractTableModel.flags(self, index)

        # logger.debug(index.row())

        if self.rows_mutable:
            if index.row() == self.dataRowCount():
                flag |= Qt.ItemIsEditable
            elif self.row_ndx.in_progress_mask.loc[index.row()]:
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
        logger.warning('`enable_mutable_rows` is Not tested')
        
        if enable:
            if self.row_ndx.is_mutable:
                return
            self.row_ndx.is_mutable = True
            self.insertRow(self.dataRowCount(), QModelIndex())
        else:
            if self.row_ndx.is_mutable == False:
                return
            self.row_ndx.is_mutable = False
            self.removeRow(self.dataRowCount(), QModelIndex())

    def add_bottom_row(self):
        bottom_row = self.null_rows(start_index=self.df.index.size, count=1)
        self.df = self.df.append(bottom_row)
        self.row_ndx.insert(self.df.size, 1)

    def null_rows(self, start_index: int, count: int) -> DF:
        nulls_row: Dict[int, Any] = self.delegate.null_value()
        data = {self.df.columns[ndx]: null_value
                for ndx, null_value in nulls_row.items()}

        nulls_df = pd.DataFrame(data=data,
                                index=range(start_index, start_index + count))
        return nulls_df

    def on_dataChanged(self, first: QModelIndex, last: QModelIndex):
        self.is_dirty = True

        # update rows in progress
        if (self.editable_columns == False).any():
            rows = range(first.row(), last.row() + 1)
            self.update_rows_in_progress(rows)

    def update_rows_in_progress(self, rows: Iterable[int]):
        if self.row_ndx.in_progress_mask.loc[rows].size == 0:
            return

    def on_rowsInserted(self, parent: QModelIndex, first: int, last: int):
        self.is_dirty = True
        self.row_ndx.insert(first, last - first)

        rows_inserted = list(range(first , last + 1))
        
        # If there are disabled columns, all inserted rows
        # gain 'row in progress' status
        if self.row_ndx.disabled_mask.any():
            self.row_ndx.in_progress_mask.iloc[rows_inserted] = True

        if self.row_ndx.non_nullable_mask.any():
            self.row_ndx.in_progress_mask.iloc[rows_inserted] = True

    def on_rowsRemoved(self, parent: QModelIndex, first: int, last: int):
        self.is_dirty = True
        self.row_ndx.remove(first, last - first)

