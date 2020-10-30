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


class Ndx():

    def __init__(self, index: pd.Index) -> None:
        self._index = index
        i_index = range(index.size)
        self._data = self._make_index_data_for(i_index)
        # TODO: add the filter mask to the index data
        self._filter_mask: SER = pd.Series(data=True, index=i_index)
        self.is_mutable = True

    @property
    def count_virtual(self) -> int:
        """Row count of the `virtual` rows at the bottom"""
        return 1 if self.is_mutable else 0

    @property
    def count_committed(self) -> int:
        """Row count of 'committed' data rows, excluding `in progress` and `virtual` rows, if any"""
        return self._data.index.size - self.count_in_progress - self.count_virtual

    @property
    def count_real(self) -> int:
        """Row count of `committed` + `in_progress` rows, excluding `virtual` rows, if any"""
        return self._data.index.size - self.count_virtual

    @property
    def size(self) -> int:
        """Row count of `committed` + `in_progress` + `virtual` rows"""
        return self._data.index.size

    @property
    def count_in_progress(self) -> int:
        """Row count of the `in progress` rows"""
        return self.in_progress_mask.sum()

    @property
    def in_progress_mask(self) -> SER:
        return self._data['in_progress']

    @property
    def disabled_mask(self) -> SER:
        return self._data['disabled']

    @property
    def non_nullable_mask(self) -> SER:
        return self._data['non_nullable']

    @property
    def filter_mask(self) -> SER:
        return self._filter_mask

    @filter_mask.setter
    def filter_mask(self, value: SER):
        self._filter_mask = value        

    @property
    def filter_mask_committed(self) -> SER:
        not_in_progress = ~self.in_progress_mask
        mask = self._filter_mask.loc[not_in_progress]        
        mask = mask.iloc[ : self.count_real] # dropping any virtual rows
        return mask

    def set_disabled_in_progress(self, index, count: int):
        self._data.loc[index, 'disabled_in_progress_count'] = count
        self._update_in_progress(index)

    def set_non_nullable_in_progress(self, index, count: int):
        self._data.loc[index, 'non_nullable_in_progress_count'] = count
        self._update_in_progress(index)

    def reduce_disabled_in_progress(self, index):
        self._data.loc[index, 'disabled_in_progress_count'] -= 1
        self._update_in_progress(index)

    def reduce_non_nullable_in_progress(self, index):
        self._data.loc[index, 'non_nullable_in_progress_count'] -= 1
        self._update_in_progress(index)

    def _update_in_progress(self, index):
        self._data.loc[index, 'in_progress'] = (
            self._data.loc[index, 'disabled_in_progress_count'] +
            self._data.loc[index, 'non_nullable_in_progress_count'] > 0)

    def insert(self, at_index: int, count: int):
        # set new index as 'not in progress' by default
        index = range(at_index, at_index + count)
        new_rows = self._make_index_data_for(index)
        self._data = pandas_obj_insert_rows(
            obj=self._data, at_index=at_index, new_rows=new_rows)

        # set new index as 'not filtered' by default
        new_rows = pd.Series(data=True, index=range(
            at_index, at_index + count))
        self._filter_mask = pandas_obj_insert_rows(
            obj=self._filter_mask, at_index=at_index, new_rows=new_rows)

    def remove(self, at_index: int, count: int):
        self._data = pandas_obj_remove_rows(
            self._data, at_index, count)
        self._filter_mask = pandas_obj_remove_rows(
            self._filter_mask, at_index, count)

    @staticmethod
    def _make_index_data_for(index) -> DF:
        '''Default 'in progress' `DataFrame` to manage the index'''
        return pd.DataFrame(
            data={'in_progress': False, 'disabled': False, 'non_nullable': False,
                  'non_nullable_in_progress_count': 0, 'disabled_in_progress_count': 0},
            index=index)
