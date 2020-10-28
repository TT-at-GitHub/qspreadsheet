import logging
import sys
import os
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.common import DF, SER, pandas_obj_insert_rows, pandas_obj_remove_rows
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class _Ndx():

    def __init__(self, size: pd.Index) -> None:
        index = range(size)
        self.index_df = self._make_index_df_for(index)
        self.filter_mask: SER = pd.Series(data=True, index=index)
        self.is_mutable = True

    @property
    def count_virtual(self) -> int:
        """Row count of the `virtual` rows (at the bottom)"""
        return 1 if self.is_mutable else 0

    @property
    def count_committed(self) -> int:
        """Row count of the 'committed' data rows (excluding `virtual` and `in progress` rows)"""
        return self.index_df.index.size - self.count_in_progress - self.count_virtual

    @property
    def count(self) -> int:
        """Row count of `committed` and `in_progress` rows"""
        return self.index_df.index.size - self.count_virtual

    @property
    def count_in_progress(self) -> int:
        """Row count of the `in progress` rows"""
        return self.in_progress_mask.sum()

    @property
    def in_progress_mask(self) -> SER:
        return self.index_df['in_progress']

    @property
    def disabled_mask(self) -> SER:
        return self.index_df['disabled']

    @property
    def non_nullable_mask(self) -> SER:
        return self.index_df['non_nullable']

    def set_disabled_in_progress(self, index, count: int):
        self.index_df.loc[index, 'disabled_in_progress_count'] = count
        self._update_in_progress(index)

    def set_non_nullable_in_progress(self, index, count: int):
        self.index_df.loc[index, 'non_nullable_in_progress_count'] = count
        self._update_in_progress(index)

    def reduce_disabled_in_progress(self, index):
        self.index_df.loc[index, 'disabled_in_progress_count'] -= 1
        self._update_in_progress(index)

    def reduce_non_nullable_in_progress(self, index):
        self.index_df.loc[index, 'non_nullable_in_progress_count'] -= 1
        self._update_in_progress(index)

    def _update_in_progress(self, index):
        self.index_df.loc[index, 'in_progress'] = (
            self.index_df.loc[index, 'disabled_in_progress_count'] +
            self.index_df.loc[index, 'non_nullable_in_progress_count'] > 0)

    def insert(self, at_index: int, count: int):
        # set new index as 'not in progress' by default
        index = range(at_index, at_index + count)
        new_rows = self._make_index_df_for(index)
        self.index_df = pandas_obj_insert_rows(
            obj=self.index_df, at_index=at_index, new_rows=new_rows)

        # set new index as 'not filtered' by default
        new_rows = pd.Series(data=True, index=range(
            at_index, at_index + count))
        self.filter_mask = pandas_obj_insert_rows(
            obj=self.filter_mask, at_index=at_index, new_rows=new_rows)

    def remove(self, at_index: int, count: int):
        self.index_df = pandas_obj_remove_rows(
            self.index_df, at_index, count)
        self.filter_mask = pandas_obj_remove_rows(
            self.filter_mask, at_index, count)

    @staticmethod
    def _make_index_df_for(index) -> DF:
        '''Default 'in progress' `DataFrame` to manage the index'''
        return pd.DataFrame(
            data={'in_progress': False, 'disabled': False, 'non_nullable': False,
                  'non_nullable_in_progress_count': 0, 'disabled_in_progress_count': 0},
            index=index)
