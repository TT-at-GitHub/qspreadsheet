import logging
import os
import sys
import traceback
from functools import partial
from itertools import groupby, count
from types import TracebackType
from typing import (Any, Iterable, List, Mapping, Optional,
                    Tuple, Type, Union, cast)

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from pandas.core import indexers

from qspreadsheet import resources_rc
from qspreadsheet.custom_widgets import ActionButtonBox
from qspreadsheet.dataframe_model import DataFrameModel
from qspreadsheet.delegates import (ColumnDelegate, MasterDelegate,
                                    automap_delegates)
from qspreadsheet.header_view import HeaderView
from qspreadsheet.menus import FilterListMenuWidget, LineEditMenuAction
from qspreadsheet.sort_filter_proxy import DataFrameSortFilterProxy
from qspreadsheet.worker import Worker
from qspreadsheet.common import DF, is_iterable
import fx

logger = logging.getLogger(__name__)


class DataFrameView(QTableView):
    '''`QTableView` to display and edit `pandas.DataFrame`

        Parameters
        ----------

        df : `pandas.DataFrame`. The data frame to manage

        delegates : [ Mapping[column, ColumnDelegate] ].  Default is 'None'.

        Column delegates used to display and edit the data.

        If no delegates are provided, `automap_delegates(df, nullable=True)` is used
        to guess the delegates, based on the column type.

        parent : [ QWidget ].  Default is 'None'. Parent for this view.
    '''

    def __init__(self, df: DF, delegates: Optional[Mapping[Any, ColumnDelegate]] = None, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)
        self.threadpool = QThreadPool(self)
        self.header_model = HeaderView(columns=df.columns.tolist())
        self.header_model.setSectionsClickable(True)
        self.setHorizontalHeader(self.header_model)
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self._main_delegate = MasterDelegate(self)
        column_delegates = delegates or automap_delegates(df, nullable=True)
        self._set_column_delegates_for_df(column_delegates, df)

        self._model = DataFrameModel(df=df, header_model=self.header_model,
                                     delegate=self._main_delegate, parent=self)

        self.proxy = DataFrameSortFilterProxy(self._model)
        self.proxy.setSourceModel(self._model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self._model.on_horizontal_scroll)
        self.verticalScrollBar().valueChanged.connect(self._model.on_vertical_scroll)
        self.set_column_widths()

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

        pos = self.mapToGlobal(event.pos())
        menu_pos = QPoint(pos.x() + 20,
                          pos.y() + menu.height() + 20)
        menu.exec_(menu_pos)

    def set_columns_edit_state(self, columns: Union[Any, Iterable[Any]], editable: bool) -> None:
        '''Enables/disables column's edit state.
            NOTE: By default all columns are editable

            Paramenters
            -----------
            columns : column or list-like. Columns to enable/disable

            editable : bool. Edit state for the columns
        '''

        if not is_iterable(columns):
            columns = [columns]

        missing = [column for column in columns
                   if column not in self.df.columns]
        if missing:
            plural = 's' if len(missing) > 1 else ''
            raise ValueError('Missing column{}: `{}`.'.format(
                plural, '`, `'.join(missing)))

        column_indices  = self._model.df.columns.get_indexer(columns)
        self._model.col_ndx.disabled_mask.iloc[column_indices] = (not editable)

    def set_column_delegate_for(self, column: Any, delegate: ColumnDelegate):
        '''Sets the column delegate for single column

            Paramenters
            -----------
            columns : Any. Column to set delegate for

            editable : ColumnDelegate. The delegate for the column
        '''
        icolumn = self.df.columns.get_loc(column)
        self._main_delegate.add_column_delegate(icolumn, delegate)

    def _set_column_delegates_for_df(self, delegates: Mapping[Any, ColumnDelegate], df: DF):
        '''(Private) Used to avoid circular reference, when calling self.df
        '''
        current = self.itemDelegate()
        if current is not None:
            current.deleteLater()

        for column, column_delegate in delegates.items():
            icolumn = df.columns.get_loc(column)
            self._main_delegate.add_column_delegate(icolumn, column_delegate)

        self.setItemDelegate(self._main_delegate)
        del current

    def set_column_delegates(self, delegates: Mapping[Any, ColumnDelegate]):
        '''Sets the column delegates for multiple columns

            Paramenters
            -----------
            delegates : Mapping[column, ColumnDelegate]. Dict-like, with column name and delegates
        '''
        self._set_column_delegates_for_df(delegates, self._model.df)

    def set_column_widths(self):
        header = self.horizontalHeader()
        for i in range(header.count()):
            header.resizeSection(
                i, self.header_model.headers[i].sizeHint().width())

    @property
    def df_model(self):
        '''Returns the model for this view

            Returns
            -------
            `DataFrameModel`
        '''
        return self._model

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
        self.proxy.set_filter_key_column(col_ndx)

        # TODO: look for other ways to position the menu
        header_pos = self.mapToGlobal(btn.parent().pos())

        # with fx.timethis(' >>>    make_header_menu'):
        menu = self.make_header_menu()

        menu_pos = QPoint(header_pos.x() + menu.width() - btn.width() + 5,
                        header_pos.y() + btn.height() + 15)

        menu.exec_(menu_pos)

    def make_cell_context_menu(self, row_ndx: int, col_ndx: int) -> QMenu:
        menu = QMenu(self)
        cell_val = self.df.iat[row_ndx, col_ndx]

        # By Value Filter
        def _quick_filter(cell_val):
            self.proxy.set_filter_key_column(col_ndx)
            self.proxy.string_filter(str(cell_val))

        menu.addAction(self._standard_icon('CommandLink'),
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
        menu.addAction(self._standard_icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)
        menu.addSeparator()
        menu.addAction("Insert Rows Above",
                       partial(self.insert_rows, 'above'))
        menu.addAction("Insert Rows Below",
                       partial(self.insert_rows, 'below'))
        menu.addSeparator()
        menu.addAction("Deleted Selected Rows",
                       self.remove_rows)
        menu.addSeparator()

        # Open in Excel
        menu.addAction("Open in Excel...", self.to_excel)

        return menu

    def make_header_menu(self) -> QMenu:
        '''Create popup menu used for header'''

        menu = QMenu(self)

        # Filter Menu Action
        str_filter = LineEditMenuAction(self, menu, 'Filter')
        str_filter.returnPressed.connect(menu.close)
        str_filter.textChanged.connect(self.proxy.string_filter)
        menu.addAction(str_filter)

        self.list_filter = FilterListMenuWidget(self, menu)
        self.list_filter.populate_list(
            column=self.df.iloc[:, self.proxy.filter_key_column],
            mask=self.proxy.accepted)


        menu.addAction(self.list_filter)
        menu.addAction(self._standard_icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)

        # Sort Ascending/Decending Menu Action
        menu.addAction(self._standard_icon('TitleBarShadeButton'),
                       "Sort Ascending",
                       partial(self.proxy.sort, self.proxy.filter_key_column, Qt.AscendingOrder))
        menu.addAction(self._standard_icon('TitleBarUnshadeButton'),
                       "Sort Descending",
                       partial(self.proxy.sort, self.proxy.filter_key_column, Qt.DescendingOrder))

        menu.addSeparator()

        # Hide
        menu.addAction("Hide Column", partial(self.hideColumn, self.proxy.filter_key_column))

        # Unhide column to left and right
        for i in (-1, 1):
            ndx = self.proxy.filter_key_column + i
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
        action_btn_box.accepted.connect(self.apply_and_close)
        action_btn_box.rejected.connect(menu.close)
        menu.addAction(action_btn_box)

        return menu

    def to_excel(self):
        worker = Worker(self._to_excel)
        worker.signals.error.connect(self.on_error)
        self.threadpool.start(worker)

    def _to_excel(self, *args, **kwargs):
        logger.info('Exporting to Excel Started...')
        from subprocess import Popen
        rows = self.proxy.accepted
        columns = self._get_visible_column_names()
        fname = 'temp.xlsx'
        logger.info('Writing to Excel file...')
        self.df.loc[rows, columns].to_excel(fname, 'Output')
        logger.info('Opening Excel...')
        Popen(fname, shell=True)
        logger.info('Exporting to Excel Finished')

    def on_error(self, exc_info: Tuple[Type[BaseException], BaseException, TracebackType]) -> None:
        logger.error(msg='ERROR.', exc_info=exc_info)
        formatted = ' '.join(traceback.format_exception(*exc_info, limit=4))
        QMessageBox.critical(self, 'ERROR.', formatted, QMessageBox.Ok)

    def _get_visible_column_names(self) -> list:
        return [self.df.columns[ndx] for ndx in range(self.df.shape[1]) if not self.isColumnHidden(ndx)]

    def _get_hidden_column_indices(self) -> list:
        return [ndx for ndx in range(self.df.shape[1]) if self.isColumnHidden(ndx)]

    def _standard_icon(self, icon_name: str) -> QIcon:
        '''Convenience function to get standard icons from Qt'''
        if not icon_name.startswith('SP_'):
            icon_name = 'SP_' + icon_name
        icon = getattr(QStyle, icon_name, None)
        if icon is None:
            raise Exception("Unknown icon {}".format(icon_name))
        return self.style().standardIcon(icon)

    def insert_rows(self, direction: str):
        indexes: List[QModelIndex] = self.selectionModel().selectedIndexes()
        rows, consecutive = _rows_from_index_list(indexes)

        def insert_consecutive(rows: List[int]):
            row = 0
            if direction == 'below':
                row = rows[-1] + 1
            elif direction == 'above':
                row = rows[0]
            else:
                raise ValueError('Unknown direction: {}'.format(str(direction)))

            # bound row number to table row size
            row = min(row, self._model.dataRowCount())
            self.model().insertRows(row, len(rows), QModelIndex())

        if consecutive:
            insert_consecutive(rows)
        else:
            groups = _consecutive_groups(rows)
            for rows in reversed(groups):
                insert_consecutive(rows)

    def remove_rows(self):
        indexes: List[QModelIndex] = self.selectionModel().selectedIndexes()
        rows, sequential = _rows_from_index_list(indexes)
        rows = [row for row in rows if row < self._model.dataRowCount()]
        if not rows:
            return False

        num_commit_to_delete = len(rows) - self._model.rows_in_progress.iloc[rows].sum()
        if self._model.commitRowCount() - num_commit_to_delete <= 0:
            logger.warning('Invalid operation: Table must have at least one data row.')
            return False

        if sequential:
            self.model().removeRows(rows[0], len(rows), QModelIndex())
        else:
            for row in reversed(rows):
                self.model().removeRows(row, 1, QModelIndex())

    def apply_and_close(self):
        menu = cast(QMenu, self.sender().parent())

        self.blockSignals(True)
        self.proxy.list_filter(self.list_filter.checked_values())
        self.blockSignals(False)
        menu.close()

def _rows_from_index_list(indexes: List[QModelIndex]) -> Tuple[List[int], bool]:
    rows = sorted(set([index.row() for index in indexes]))
    consecutive = rows[0] + len(rows) - 1 == rows[-1]
    return rows, consecutive

def _consecutive_groups(data: List[int]) -> List[List[int]]:
    groups = []
    for _, g in groupby(data, lambda n, c=count(): n-next(c)):
        groups.append(list(g))
    return groups