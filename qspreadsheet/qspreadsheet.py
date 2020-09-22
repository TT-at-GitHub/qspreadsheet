from logging import Logger
import operator
import os
from qspreadsheet.delegates import ColumnDelegate, GenericDelegate, automap_delegates
import sys
from functools import partial
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union
import logging

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet import richtextlineedit
from qspreadsheet import delegates
from qspreadsheet.sort_filter_proxy import DataFrameSortFilterProxy
from qspreadsheet import LEFT
from qspreadsheet.custom_widgets import LabeledTextEdit, LabeledLineEdit, ActionButtonBox
from qspreadsheet.menus import LineEditMenuAction, FilterListMenuWidget
from qspreadsheet.header import HeaderView, HeaderWidget
from qspreadsheet.sort_filter_proxy import DataFrameSortFilterProxy

Logger = logging.getLogger(__name__)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame, header_model: HeaderView,
                 delegate: ColumnDelegate, parent: Optional[QWidget] = None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.df = df.copy()
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
            return self.delegate.background_brush(index)
        if role == Qt.ForegroundRole:
            return self.delegate.foreground_brush(index)
        if role == Qt.FontRole:
            return self.delegate.font(index)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                            Qt.ItemIsEditable)

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


class DataFrameView(QTableView):

    def __init__(self, df: pd.DataFrame, delegates: Optional[Mapping[Any, ColumnDelegate]] = None, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)

        self.header_model = HeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self.header_model)
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self._main_delegate = GenericDelegate(self)
        self._model = DataFrameModel(df=df, header_model=self.header_model,
                                     delegate=self._main_delegate, parent=self)

        delegates = delegates or automap_delegates(df)
        self.set_column_delegates(delegates)
        self.proxy = DataFrameSortFilterProxy(self)
        self.proxy.set_df(df)
        self.proxy.setSourceModel(self._model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self._model.on_horizontal_scroll)
        self.verticalScrollBar().valueChanged.connect(self._model.on_vertical_scroll)
        self.set_column_widths()

    def set_column_delegate_for(self, column: Any, delegate: ColumnDelegate):
        icolumn = self.df.columns.get_loc(column)
        self._main_delegate.add_column_delegate(icolumn, delegate)

    def set_column_delegates(self, delegates: Mapping[Any, ColumnDelegate]):
        current = self.itemDelegate()
        if current is not None:
            current.deleteLater()

        for column, column_delegate in delegates.items():
            icolumn = self.df.columns.get_loc(column)
            self._main_delegate.add_column_delegate(icolumn, column_delegate)

        self.setItemDelegate(self._main_delegate)
        del current

    def set_column_widths(self):
        header = self.horizontalHeader()
        for i in range(header.count()):
            header.resizeSection(
                i, self.header_model.headers[i].sizeHint().width())

    @property
    def df(self) -> pd.DataFrame:
        return self._model.df

    def set_df(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise TypeError('Invalid type for `df`. Expected DataFrame')
        self._model.df = df

    def filter_clicked(self, name: str):
        btn = self.header_model.filter_btn_mapper.mapping(name)

        col_ndx = self.df.columns.get_loc(name)
        self.proxy.setFilterKeyColumn(col_ndx)

        # TODO: look for other ways to position the menu
        header_pos = self.mapToGlobal(btn.parent().pos())
        menu = self.make_header_menu(col_ndx)
        menu_pos = QPoint(header_pos.x() + menu.width() - btn.width() + 5,
                          header_pos.y() + btn.height() + 15)
        menu.exec_(menu_pos)

    def make_cell_context_menu(self, row_ndx: int, col_ndx: int) -> QMenu:
        menu = QMenu(self)
        cell_val = self.df.iat[row_ndx, col_ndx]

        # By Value Filter
        def _quick_filter(cell_val):
            self.proxy.setFilterKeyColumn(col_ndx)
            self.proxy.string_filter(str(cell_val))

        menu.addAction(self._icon('CommandLink'),
                       "Filter By Value", partial(_quick_filter, cell_val))

        # GreaterThan/LessThan filter
        def _cmp_filter(s_col, op):
            return op(s_col, cell_val)
        # menu.addAction("Filter Greater Than",
        #                 partial(self._data_model.filterFunction, col_ndx=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.ge)))
        # menu.addAction("Filter Less Than",
        #                 partial(self._data_model.filterFunction, col_ndx=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.le)))
        menu.addAction(self._icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)
        menu.addSeparator()

        # Open in Excel
        menu.addAction("Open in Excel...", self._to_excel)

        return menu

    def sizeHint(self) -> QSize:
        width = 0
        for i in range(self.df.shape[1]):
            width += self.columnWidth(i)
        width += self.verticalHeader().sizeHint().width()
        width += self.verticalScrollBar().sizeHint().width()
        width += self.frameWidth() * 2

        return QSize(width, self.height())

    def contextMenuEvent(self, event: QContextMenuEvent):
        '''Implements right-clicking on cell.

            NOTE: You probably want to overrite make_cell_context_menu, not this
            function, when subclassing.
        '''
        row_ndx = self.rowAt(event.y())
        col_ndx = self.columnAt(event.x())

        if row_ndx < 0 or col_ndx < 0:
            return  # out of bounds

        menu = self.make_cell_context_menu(row_ndx, col_ndx)
        menu.exec_(self.mapToGlobal(event.pos()))

    def make_header_menu(self, col_ndx: int) -> QMenu:
        '''Create popup menu used for header'''

        menu = QMenu(self)

        # Filter Menu Action
        str_filter = LineEditMenuAction(self, menu, 'Filter')
        str_filter.returnPressed.connect(menu.close)
        str_filter.textChanged.connect(self.proxy.string_filter)
        menu.addAction(str_filter)

        list_filter = FilterListMenuWidget(self, menu, col_ndx)
        menu.addAction(list_filter)
        menu.addAction(self._icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)

        # Sort Ascending/Decending Menu Action
        menu.addAction(self._icon('TitleBarShadeButton'),
                       "Sort Ascending",
                       partial(self.proxy.sort, col_ndx, Qt.AscendingOrder))
        menu.addAction(self._icon('TitleBarUnshadeButton'),
                       "Sort Descending",
                       partial(self.proxy.sort, col_ndx, Qt.DescendingOrder))

        menu.addSeparator()

        # Hide
        menu.addAction("Hide Column", partial(self.hideColumn, col_ndx))

        # Unhide column to left and right
        for i in (-1, 1):
            ndx = col_ndx + i
            if self.isColumnHidden(ndx):
                menu.addAction(f'Unhide {self.df.columns[ndx]}',
                               partial(self.showColumn, ndx))

        # Unhide all hidden columns
        def _unhide_all(hidden_indices: list):
            for ndx in hidden_indices:
                self.showColumn(ndx)
        hidden_indices = self._get_hidden_column_indices()
        if hidden_indices:
            menu.addAction(f'Unhide All',
                           partial(_unhide_all, hidden_indices))

        menu.addSeparator()

        # Filter Button box
        action_btn_box = ActionButtonBox(menu)
        action_btn_box.accepted.connect(list_filter.apply_and_close)
        action_btn_box.rejected.connect(menu.close)
        menu.addAction(action_btn_box)

        return menu

    def _to_excel(self):
        from subprocess import Popen
        rows = self.proxy.accepted_mask
        columns = self._get_visible_column_names()
        fname = 'temp.xlsx'
        self.df.loc[rows, columns].to_excel(fname, 'Output')
        Popen(fname, shell=True)

    def _get_visible_column_names(self) -> list:
        return [self.df.columns[ndx] for ndx in range(self.df.shape[1]) if not self.isColumnHidden(ndx)]

    def _get_hidden_column_indices(self) -> list:
        return [ndx for ndx in range(self.df.shape[1]) if self.isColumnHidden(ndx)]

    def _icon(self, icon_name: str) -> QIcon:
        '''Convenience function to get standard icons from Qt'''
        if not icon_name.startswith('SP_'):
            icon_name = 'SP_' + icon_name
        icon = getattr(QStyle, icon_name, None)
        if icon is None:
            raise Exception("Unknown icon {}".format(icon_name))
        return self.style().standardIcon(icon)


