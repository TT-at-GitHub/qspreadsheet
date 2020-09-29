import logging
import sys
import os
from typing import Any, List, Optional, Union

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
        self.delegate = delegate
        self.df = df.copy()
        self.add_bottom_row()

        self.rows_in_progress = pd.Series(data=False, index=self.df.index)
        self.filter_mask = pd.Series(data=True, index=self.df.index)

        self.editable_columns = pd.Series(index=df.columns, data=True)

        self.header_model = header_model
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self.filter_values_mapper = QSignalMapper(self)

        self.rows_mutable = 1
        self.is_dirty = False

    def progressRowCount(self) -> int:
        return self.rows_in_progress.sum()

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
            logger.warning('index.row() < 0')
            breakpoint()
        
        if role == Qt.DisplayRole:
            if index.row() == self.dataRowCount():
                return ''
            return self.delegate.display_data(index,
                                              self.df.iloc[index.row(), index.column()])

        if role == Qt.EditRole:
            if index.row() == self.dataRowCount():
                return self.delegate.default_value(index)
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

        if index.row() == self.dataRowCount():
            self.insertRow(index.row(), index)

        self.df.iloc[index.row(), index.column()] = value

        self.is_dirty = True
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:

        if section < 0:
            logger.warning('section: {}'.format(section))
            breakpoint()
            return None

        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if section == self.dataRowCount():
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

        new_rows = self.null_rows(start_index=row, count=count)
        self.df = self.pandas_obj_insert_rows(self.df, row, new_rows)

        new_rows = pd.Series(data=True, index=range(row, row + count))
        self.rows_in_progress = self.pandas_obj_insert_rows(
            obj=self.rows_in_progress, at_index=row, new_rows=new_rows)

        self.filter_mask = self.pandas_obj_insert_rows(
            obj=self.filter_mask, at_index=row, new_rows=new_rows)

        self.endInsertRows()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex) -> bool:        
        logger.debug('removeRows(first:{}, last:{}), num rows: {}'.format(
            row, row + count - 1, count))
        self.beginRemoveRows(parent, row, row + count - 1)
        self.df = self.drop_pandas_obj_rows(self.df, row, count)
        self.rows_in_progress = self.drop_pandas_obj_rows(self.rows_in_progress, row, count)
        self.filter_mask = self.drop_pandas_obj_rows(self.filter_mask, row, count)
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
        raise NotImplementedError('enable_mutable_rows()')
        if enable:
            if self.rows_mutable == 1:
                return
            self.rows_mutable = 1
            self.add_bottom_row()
        else:
            if self.rows_mutable == 0:
                return
            self.rows_mutable = 0
            self.df = self.df.drop(index=self.df.index[-1])

    def add_bottom_row(self):
        bottom_row = self.null_rows(start_index=self.df.index.size, count=1)
        self.df = self.df.append(bottom_row)

    def drop_pandas_obj_rows(self, obj: Union[DF, SER], row: int, count: int) -> Union[DF, SER]:
        index_rows = range(row, row + count)
        obj = obj.drop(index=obj.index[index_rows])
        obj = obj.reset_index(drop=True)
        return obj

    def pandas_obj_insert_rows(self, obj: Union[DF, SER], at_index: int, 
                               new_rows: Union[DF, SER]) -> Union[DF, SER]:
        above = obj.iloc[0 : at_index]
        below = obj.iloc[at_index : ]
        below.index = below.index + new_rows.index.size
        obj = pd.concat([above, new_rows, below])
        return obj

    def null_rows(self, start_index: int, count: int) -> DF:
        nulls_row: List = self.delegate.null_value()
        data = [nulls_row for _ in range(count)]

        nulls_df = pd.DataFrame(data=data, columns=self.df.columns, 
                                index=range(start_index, start_index + count))
        return nulls_df
