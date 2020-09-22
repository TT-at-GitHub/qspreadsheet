import logging
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet import DF

logger = logging.getLogger(__name__)



class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._df = pd.DataFrame()
        self.accepted_mask = pd.Series()
        self._masks_cache = []

    def set_df(self, df: DF):
        self._df = df
        self.accepted_mask = self._alltrues()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row < self.accepted_mask.size:
            return self.accepted_mask.iloc[source_row]
        return True

    def string_filter(self, text: str):
        text = text.lower()
        colname = self._colname()
        if not text:
            mask = self._alltrues()
        else:
            mask = self._df[colname].astype(
                'str').str.lower().str.contains(text)

        self.accepted_mask = mask
        self.invalidate()

    def list_filter(self, values):
        colname = self._colname()
        mask = self._df[colname].apply(str).isin(values)
        self.accepted_mask = mask
        self.invalidate()

    def reset_filter(self):
        self.accepted_mask = self._alltrues()
        self.invalidateFilter()

    def _colname(self) -> str:
        return self._df.columns[self.filterKeyColumn()]

    def _alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._df.index)

    def unique_values(self) -> List[Any]:
        result = []
        for i in range(self.rowCount()):
            index = self.index(i, self.filterKeyColumn())
            val = self.data(index, Qt.DisplayRole)
            result.append(val)
        return result
