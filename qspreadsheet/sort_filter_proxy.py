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
        self._model = None

        self._masks_cache = []
        self._column_index = 0
        self._list_filter_widget = None
        self._pool = QThreadPool(self)
        
        #FIXME: re-design these in to the masks cache...!
        self.mask = pd.Series()
        self.unique = pd.Series()

    def list_filter_widget(self):
        self._list_filter_widget = FilterListMenuWidget(self)
        self._list_filter_widget.show_all_btn.clicked.connect(self._refill_list)
        return self._list_filter_widget

    def setSourceModel(self, model):
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
        if source_row < self.accepted.size:
            return self.accepted.iloc[source_row]
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
        values = self._list_filter_widget.checked_values()
        mask = self._model._df.iloc[: , self.filter_key_column].apply(str).isin(values)
        self.set_accepted(mask)
        self.invalidate()

    def reset_filter(self):
        # Nothing to reset
        if self.accepted.all():
            return
            
        self.set_accepted(self._alltrues())
        self.invalidate()
        # self.invalidateFilter()

    def _alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._model._df.index)

    def unique_values(self) -> List[Any]:
        result = []
        for i in range(self.rowCount()):
            index = self.index(i, self.filter_key_column)
            val = self.data(index, Qt.DisplayRole)
            result.append(val)
        return result
    
    def populate_list(self):
        self._list_filter_widget.list.clear()

        self.unique, self.mask = self._model.get_filter_values_for(self._column_index)

        # Add a (Select All)
        if self.mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        item = QListWidgetItem('(Select All)')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(select_all_state)
        self._list_filter_widget.list.addItem(item)
        self._list_filter_widget._action_select_all = item

        if self.unique.size > INITIAL_FILTER_LIMIT:            
            sliced_unique = self.unique.iloc[ : INITIAL_FILTER_LIMIT]
            self.add_list_items(sliced_unique)
            self._list_filter_widget.show_all_btn.setVisible(True)
        else:
            self.add_list_items(self.unique)

    def add_list_items(self, values: SER, **kwargs):
        """
            values : {pd.Series}: values to add to the list
            
            mask : {pd.Series}: bool mask showing if item is visible
            
            **kwargs : {dict}: to hold the `progress_callback` from Worker
        """

        for row_ndx, val in values.items():
            
            index = self._model.createIndex(row_ndx, self._column_index)
            value = self._model.delegate.display_data(index, val)
            state = Qt.Checked if self.mask.iloc[row_ndx] else Qt.Unchecked
            
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(state)
            self._list_filter_widget.list.addItem(item)

    def _refill_list(self):
        btn = self.sender()
        worker = Worker(func=self.add_list_items, 
            values=self.unique.iloc[INITIAL_FILTER_LIMIT :])
        worker.signals.error.connect(self.parent().on_error)
        worker.signals.result.connect(lambda: btn.setVisible(False))
        worker.signals.about_to_start.connect(lambda: btn.setEnabled(False))
        worker.signals.finished.connect(lambda: btn.setEnabled(True))
        # worker.run()
        self._pool.start(worker)