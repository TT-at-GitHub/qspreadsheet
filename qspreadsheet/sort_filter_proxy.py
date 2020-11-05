import logging
from logging import log
import os
import traceback

from numpy.lib.function_base import disp
from qspreadsheet.worker import Worker

from numpy.core.fromnumeric import alltrue, size
from qspreadsheet.dataframe_model import DataFrameModel
import sys
from typing import Any, Dict, Generator, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet.common import DF, SER
from qspreadsheet._ndx import _Ndx
from qspreadsheet.menus import FilterListWidgetAction

logger = logging.getLogger(__name__)

INITIAL_FILTER_LIMIT = 4 # 5000
FILTER_VALUES_STEP = 3 # 1000

class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, model: DataFrameModel, parent: Optional[QWidget]=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._model: DataFrameModel = model
        self._model.rowsInserted.connect(self.on_rows_inserted)
        self._model.rowsRemoved.connect(self.on_rows_removed)     

        self._column_index = 0
        self._list_widget = None
        self._pool = QThreadPool(self)
        
        #FIXME: re-design these in to the masks cache...!
        self._display_values: Optional[SER] = None
        self._filter_values: Optional[SER] = None
        self._display_values_gen = None
        self.filter_cache: Dict[int, SER] = {-1 : self.alltrues()}
        self.accepted = self.alltrues()

    def create_list_filter_widget(self) -> FilterListWidgetAction:
        if self._list_widget:
            self._list_widget.deleteLater()
        self._list_widget = FilterListWidgetAction(self)
        self._list_widget.show_all_btn.clicked.connect(
            self.show_all_filter_values)
        return self._list_widget

    @property
    def filter_key_column(self) -> int:
        return self._column_index

    def set_filter_key_column(self, value: int):
        self._column_index = value

    def add_filter_mask(self, mask: SER):
        if self._column_index in self.filter_cache:
            self.filter_cache.pop(self._column_index)
        self.filter_cache[self._column_index] = mask
        # update accepted
        self._update_accepted(mask)

    def remove_filter_mask(self, column_index):
        if column_index in self.filter_cache:
            self.filter_cache.pop(column_index)
        self._update_accepted(self.filter_mask)
    
    def _update_accepted(self, mask: SER):
        self.accepted.loc[:] = False
        self.accepted.loc[mask.index] = mask

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row < self.accepted.size:
            return self.accepted.iloc[source_row]
        return True

    def string_filter(self, text: str):

        unique, _ = self.get_unique_model_values()
        self._display_values = pd.Series({
            ndx : self._model.delegate.display_data(self._model.index(ndx, self._column_index), value) 
            for ndx, value in unique.items()})
        self._filter_values = self._display_values.drop_duplicates()

        if text:
            mask = self._filter_values.str.lower().str.contains(text.lower())
            filter_values = self._filter_values.loc[mask]
        else:
            filter_values = self._filter_values

        mask = self._display_values.isin(filter_values)
        self.add_filter_mask(mask)
        self.invalidateFilter()

    def filter_list_widget_by_text(self, text: str):
        if text:
            mask = self._filter_values.str.lower().str.contains(text.lower())
            filter_values = self._filter_values.loc[mask]
        else:
            filter_values = self._filter_values
            
        self._list_widget.list.clear()
        item = QListWidgetItem('(Select All)')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self._list_widget.select_all_item = item
        self._list_widget.list.addItem(item)

        for _, value in filter_values.items():
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self._list_widget.list.addItem(item)        

    def apply_list_filter(self):
        select_all = self._list_widget.select_all_item
        
        if (select_all.checkState() == Qt.Checked):
            self.remove_filter_mask(self._column_index)
        else:
            checked_values = self._list_widget.values()
            mask = self._display_values.isin(checked_values)
            self.add_filter_mask(mask)
        self.invalidateFilter()

    def clear_filter_cache(self):
        if not self.is_data_filtered:
            return
        self.filter_cache.clear()
        self.filter_cache = {-1 : self.alltrues()}
        self.accepted = self.alltrues()
        self.invalidateFilter()

    def clear_filter_column(self, column_index: int):
        self.remove_filter_mask(column_index)
        self.invalidateFilter()

    def refill_list(self, *args, **kwargs):
        """ Adds to the filter list all remaining values, 
            over the initial filter limit

            NOTE: *args, **kwargs signature is required by Worker
        """
        display_values = pd.Series({ndx : value for ndx, value in self._display_values_gen})
        filter_index = display_values.str.lower().drop_duplicates().index
        filter_values = display_values.loc[filter_index]
        self._display_values = self._display_values.append(display_values)
        
        try:
            filter_values = filter_values.sort_values()
        except:
            pass

        self._filter_values = self._filter_values.append(filter_values)
        self.add_list_items(filter_values)

    def async_populate_list(self):
        worker = Worker(func=self.populate_list)
        worker.signals.error.connect(self.parent().on_error)
        # worker.run()
        self._pool.start(worker)

    def populate_list(self, *args, **kwargs):
        self._list_widget.list.clear()

        import fx

        unique, mask = self.get_unique_model_values()
        
        # Generator for display filter values
        self._display_values_gen = (
            (ndx ,self._model.delegate.display_data(self._model.index(ndx, self._column_index), value))
            for ndx, value in unique.items())

        if unique.size <= INITIAL_FILTER_LIMIT:
            self._display_values = pd.Series({ndx : value for ndx, value in self._display_values_gen})
            unique_index = self._display_values.str.lower().drop_duplicates().index
            self._filter_values = self._display_values.loc[unique_index] 
        else:
            self._display_values = pd.Series(name=unique.name)
            self._filter_values = pd.Series(name=unique.name)
            
            next_step = INITIAL_FILTER_LIMIT
            remaining = unique.size

            while next_step and self._filter_values.size < INITIAL_FILTER_LIMIT:
                # print('next_step {}, remaining {}'.format(next_step, remaining))
                values = pd.Series(dict(next(self._display_values_gen) 
                                for _ in range(next_step)))
                self._display_values = self._display_values.append(values)
                unique_index = values.str.lower().drop_duplicates().index
                self._filter_values = self._filter_values.append(values.loc[unique_index])
                remaining -= next_step
                remaining = max(remaining, 0)
                next_step = min(FILTER_VALUES_STEP, remaining)

            if remaining:
                self._list_widget.show_all_btn.setVisible(True)

            # print('display_values.size', self._display_values.size)
            # print('self._filter_values.size', self._filter_values.size)
            # print( 'remaining', remaining)
 
        try:
            self._filter_values = self._filter_values.sort_values()
        except:
            pass

        # Add a (Select All)
        if mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        item = QListWidgetItem('(Select All)')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(select_all_state)
        self._list_widget.list.addItem(item)
        self._list_widget.select_all_item = item
        self.add_list_items(self._filter_values)

    def add_list_items(self, values: SER):
        """values : {pd.Series}: values to add to the list
        """
        for row_ndx, value in values.items():
            state = Qt.Checked if self.accepted.loc[row_ndx] else Qt.Unchecked
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(state)
            self._list_widget.list.addItem(item)

    def show_all_filter_values(self):
        btn = self.sender()
        worker = Worker(func=self.refill_list)
        worker.signals.error.connect(self.parent().on_error)
        worker.signals.result.connect(lambda: btn.setVisible(False))
        worker.signals.about_to_start.connect(lambda: btn.setEnabled(False))
        worker.signals.finished.connect(lambda: btn.setEnabled(True))
        # worker.run()
        self._pool.start(worker)

    def get_unique_model_values(self) -> Tuple[SER, SER]:
        # Generates filter items for given column index
        column: SER = self._model.df.iloc[:, self._column_index]
        
        # if the column being filtered is not the last filtered column
        filter_mask = self.filter_mask
        if self._column_index != self.last_filter_index:
            filter_mask = filter_mask.loc[filter_mask]
        column = column.loc[filter_mask.index]
        unique = column.drop_duplicates()

        return unique, filter_mask

    @property
    def is_data_filtered(self) -> bool:
        return len(self.filter_cache) > 1

    @property
    def filter_mask(self) -> SER:
        return self.filter_cache[self.last_filter_index]

    @property
    def last_filter_index(self) -> int:
        return list(self.filter_cache.keys())[-1]

    def is_column_filtered(self, col_ndx: int) -> bool:
        return col_ndx in self.filter_cache

    def alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._model.df.index)

    def on_rows_inserted(self, parent: QModelIndex, first: int, last: int):
        pass

    def on_rows_removed(self, parent: QModelIndex, first: int, last: int):
        pass