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
from qspreadsheet.menus import FilterListMenuWidget

logger = logging.getLogger(__name__)

INITIAL_FILTER_LIMIT = 5000


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._model: Optional[DataFrameModel] = None

        self._masks_cache = []
        self._column_index = 0
        self._list_filter_widget = None
        self._pool = QThreadPool(self)
        
        #FIXME: re-design these in to the masks cache...!
        self._display_values: Optional[SER] = None
        self._filter_values: Optional[SER] = None
        self._over_limit_values: Optional[SER] = None

    def list_filter_widget(self):
        self._list_filter_widget = FilterListMenuWidget(self)
        self._list_filter_widget.show_all_btn.clicked.connect(
            self.show_all_filter_values)
        return self._list_filter_widget

    def setSourceModel(self, model: DataFrameModel):
        self._model = model
        super().setSourceModel(model)

    @property
    def filter_key_column(self) -> int:
        # filterKeyColumn
        return self._column_index

    def set_filter_key_column(self, value: int):
        self._column_index = value

    @property
    def accepted(self) -> SER:
        return self._model.row_ndx.filter_mask

    def set_accepted(self, accepted):
        self._model.row_ndx.filter_mask = accepted

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row < self._model.row_ndx.filter_mask.size:
            return self._model.row_ndx.filter_mask.iloc[source_row]
        return True

    def string_filter(self, text: str):
        text = text.lower()
        if not text:
            mask = self._alltrues()
        else:
            mask = self._model._df.iloc[: , self.filter_key_column].astype(
                'str').str.lower().str.contains(text)

        self.set_accepted(mask)
        self.invalidate()

    def apply_list_filter(self):
        print(self._display_values)
        checked_values = self._list_filter_widget.checked_values()
        filter_values = self._display_values.loc[checked_values]
        print(filter_values)

        mask = self.accepted
        mask.loc[filter_values.index] = True
        self.set_accepted(mask)
        self.invalidateFilter()

    def reset_filter(self):
        # Nothing to reset
        if self.accepted.all():
            return
            
        self.set_accepted(self._alltrues())
        self.invalidateFilter()
        # self.invalidateFilter()

    def _alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._model._df.index)

    def refill_list(self, *args, **kwargs):
        """ Adds to the filter list all remaining values, 
            over the initial filter limit

            NOTE: *args, **kwargs signature is required by Worker
        """
        display_values = pd.Series({ndx : self._model.delegate.display_data(self._model.index(ndx, self._column_index), value) 
            for ndx, value in self._over_limit_values.items()})
        self._display_values = self._display_values.add(display_values)
        self._filter_values = self._filter_values.add(display_values.drop_duplicates())
        self.add_list_items(self._filter_values)

    def populate_list(self):
        self._list_filter_widget.list.clear()

        unique = self.get_unique_model_values()
        if unique.size > INITIAL_FILTER_LIMIT:
            unique = unique.iloc[ : INITIAL_FILTER_LIMIT]
            self._over_limit_values = unique.iloc[ INITIAL_FILTER_LIMIT :]
            self._list_filter_widget.show_all_btn.setVisible(True)

        self._display_values = pd.Series({ndx : self._model.delegate.display_data(self._model.index(ndx, self._column_index), value) 
            for ndx, value in unique.items()})
        self._filter_values = self._display_values.drop_duplicates()

        mask = self._model.row_ndx.filter_mask_committed

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
        mask = self.accepted

        for row_ndx, value in values.items():

            state = Qt.Checked if mask.loc[row_ndx] else Qt.Unchecked
            
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

    def get_unique_model_values(self) -> SER:
        # Generates filter items for given column index
        column: SER = self._model._df.iloc[:, self._column_index]

        # dropping the rows in progress from the column and the mask
        not_inprogress_mask = ~self._model.row_ndx.in_progress_mask
        column = column.loc[not_inprogress_mask]
        column = column.iloc[: self._model.row_ndx.count_real]

        unique = column.drop_duplicates()
                
        try:
            unique = unique.sort_values()
        except:
            pass

        return unique