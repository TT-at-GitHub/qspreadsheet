import logging
import os

from numpy.core.fromnumeric import alltrue
from qspreadsheet.dataframe_model import DataFrameModel
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.common import DF, SER
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent: Optional[DataFrameModel]=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._parent = None
        
        if parent is not None:
            self.setParent(parent)
        self._masks_cache = []
        self._filter_key_column = 0

    def setParent(self, parent: DataFrameModel):
        self._parent = parent
        super().setParent(parent)

    @property
    def filter_key_column(self) -> int:
        return self._filter_key_column

    def set_filter_key_column(self, value: int):
        self._filter_key_column = value

    @property
    def accepted(self) -> SER:
        return self._parent.row_ndx.filter_mask

    def set_accepted(self, accepted):
        self._parent.row_ndx.filter_mask = accepted

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row < self.accepted.size:
            return self.accepted.iloc[source_row]
        return True

    def string_filter(self, text: str):
        text = text.lower()
        if not text:
            mask = self._alltrues()
        else:
            mask = self._parent._df.iloc[: , self.filter_key_column].astype(
                'str').str.lower().str.contains(text)

        self.set_accepted(mask)
        self.invalidate()

    def list_filter(self, values):
        mask = self._parent._df.iloc[: , self.filter_key_column].apply(str).isin(values)
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
        return pd.Series(data=True, index=self._parent._df.index)

    def unique_values(self) -> List[Any]:
        result = []
        for i in range(self.rowCount()):
            index = self.index(i, self.filter_key_column)
            val = self.data(index, Qt.DisplayRole)
            result.append(val)
        return result