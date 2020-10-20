import logging
import os
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

    def setParent(self, parent: DataFrameModel):
        self._parent = parent
        super().setParent(parent)

    @property
    def accepted(self):
        return self._parent.row_ndx.filter_mask

    @accepted.setter
    def accepted(self, accepted):
        self._parent.row_ndx.filter_mask = accepted

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row < self.accepted.size:
            return self.accepted.iloc[source_row]
        return True

    def string_filter(self, text: str):
        text = text.lower()
        colname = self._colname()
        if not text:
            mask = self._alltrues()
        else:
            mask = self._parent.df[colname].astype(
                'str').str.lower().str.contains(text)

        self.accepted = mask
        self.invalidate()

    def list_filter(self, values):
        colname = self._colname()
        mask = self._parent.df[colname].apply(str).isin(values)
        self.accepted = mask
        self.invalidate()

    def reset_filter(self):
        self.accepted = self._alltrues()
        self.invalidateFilter()

    def _colname(self) -> str:
        return self._parent.df.columns[self.filterKeyColumn()]

    def _alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._parent.df.index)

    def unique_values(self) -> List[Any]:
        result = []
        for i in range(self.rowCount()):
            index = self.index(i, self.filterKeyColumn())
            val = self.data(index, Qt.DisplayRole)
            result.append(val)
        return result