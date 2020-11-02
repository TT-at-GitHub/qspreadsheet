import logging
import os
import traceback
from qspreadsheet.worker import Worker

from numpy.core.fromnumeric import alltrue
from qspreadsheet.dataframe_model import DataFrameModel
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet.common import DF, SER
from qspreadsheet._ndx import _Ndx
from qspreadsheet.menus import FilterListMenuWidget

logger = logging.getLogger(__name__)

INITIAL_FILTER_LIMIT = 5000


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, model: DataFrameModel, parent: Optional[QWidget]=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._model: DataFrameModel = model
        self._model.rowsInserted.connect(self.on_rows_inserted)
        self._model.rowsRemoved.connect(self.on_rows_removed)     

        self._column_index = 0
        self._list_filter_widget = None
        self._pool = QThreadPool(self)
        
        #FIXME: re-design these in to the masks cache...!
        self._display_values: Optional[SER] = None
        self._filter_values: Optional[SER] = None
        self._over_limit_values: Optional[SER] = None

        self.filter_cache: Dict[int, SER] = {-1 : self.alltrues()}
        self.accepted = self.alltrues()

    def list_filter_widget(self):
        self._list_filter_widget = FilterListMenuWidget(self)
        self._list_filter_widget.show_all_btn.clicked.connect(
            self.show_all_filter_values)
        return self._list_filter_widget

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
        text = text.lower()
        raise NotImplementedError('string_filter')
        if not text:
            mask = self.alltrues()
        else:
            mask = self._display_values.str.contains(text)

        self.set_filter_mask(mask)
        self.invalidateFilter()

    def apply_list_filter(self):
        checked_values, select_all = self._list_filter_widget.values()
        mask = self._display_values.isin(checked_values)
        # filter_values = self._display_values.loc[mask]

        if select_all:
            self.remove_filter_mask(self._column_index)
        else:
            self.add_filter_mask(mask)
        self.invalidateFilter()

    def clear_filter(self):
        if not self.is_filtered:
            return
        self.filter_cache.clear()
        self.filter_cache = {-1 : self.alltrues()}
        self.accepted = self.alltrues()        
        self.invalidateFilter()

    def refill_list(self, *args, **kwargs):
        """ Adds to the filter list all remaining values, 
            over the initial filter limit

            NOTE: *args, **kwargs signature is required by Worker
        """
        display_values = pd.Series({ndx : self._model.delegate.display_data(self._model.index(ndx, self._column_index), value) 
            for ndx, value in self._over_limit_values.items()})
        self._display_values = self._display_values.append(display_values)
        self._filter_values = self._filter_values.append(display_values.drop_duplicates())
        self.add_list_items(self._filter_values)

    def populate_list(self):
        self._list_filter_widget.list.clear()

        unique, mask = self.get_unique_model_values()
        if unique.size > INITIAL_FILTER_LIMIT:
            self._over_limit_values = unique.iloc[ INITIAL_FILTER_LIMIT :]
            unique = unique.iloc[ : INITIAL_FILTER_LIMIT]
            self._list_filter_widget.show_all_btn.setVisible(True)

        self._display_values = pd.Series({ndx : self._model.delegate.display_data(self._model.index(ndx, self._column_index), value) 
            for ndx, value in unique.items()})
        self._filter_values = self._display_values.drop_duplicates()

        # Add a (Select All)
        if mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        item = QListWidgetItem('(Select All)')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(select_all_state)
        self._list_filter_widget.list.addItem(item)
        self._list_filter_widget._action_select_all = item
        self.add_list_items(self._filter_values)

    def add_list_items(self, values: SER):
        """values : {pd.Series}: values to add to the list
        """
        for row_ndx, value in values.items():
            state = Qt.Checked if self.accepted.loc[row_ndx] else Qt.Unchecked
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(state)
            self._list_filter_widget.list.addItem(item)

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

        try:
            unique = unique.sort_values()
        except:
            pass

        return unique, filter_mask

    @property
    def filter_mask(self) -> SER:
        mask = self.filter_cache[self.last_filter_index]
        return mask

    @property
    def last_filter_index(self) -> int:
        return list(self.filter_cache.keys())[-1]

    @property
    def is_filtered(self) -> bool:
        return len(self.filter_cache) > 1

    def alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._model.df.index)

    def on_rows_inserted(self, parent: QModelIndex, first: int, last: int):
        pass

    def on_rows_removed(self, parent: QModelIndex, first: int, last: int):
        pass