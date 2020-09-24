import logging
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.custom_widgets import LabeledLineEdit
from qspreadsheet import LEFT
from qspreadsheet import resources_rc

logger = logging.getLogger(__name__)


class LineEditMenuAction(QWidgetAction):
    '''Labeled Textbox in menu'''

    def __init__(self, parent, menu, label_text='', position=LEFT):
        super(LineEditMenuAction, self).__init__(parent)

        widget = LabeledLineEdit(label_text, position, parent=menu)
        self.returnPressed = widget.lineEdit.returnPressed
        self.textChanged = widget.lineEdit.textChanged
        self.setDefaultWidget(widget)


class FilterListMenuWidget(QWidgetAction):
    '''Checkboxed list filter menu'''

    def __init__(self, parent, menu: QMenu, col_ndx: int) -> None:
        '''Checkbox list filter menu

            Arguments
            ----------
            
            parent: (Widget)
                Parent
            
            menu: (QMenu)
                Menu object this list is located on
            
            col_ndx: (int)
                Column index to filter
            
            label: (str)
                Label in popup menu
        '''
        super(FilterListMenuWidget, self).__init__(parent)

        # State
        self.menu = menu
        self.col_ndx = col_ndx

        # Build Widgets
        widget = QWidget()
        layout = QVBoxLayout()
        self.list = QListWidget()
        self.list.setStyleSheet('''
            QListView::item:selected {
                background: rgb(195, 225, 250);
                color: rgb(0, 0, 0);
            } ''')
        self.list.setFixedHeight(100)

        layout.addWidget(self.list)
        widget.setLayout(layout)

        self.setDefaultWidget(widget)

        # Signals/slots
        self.list.itemChanged.connect(self.on_listitem_changed)
        self.parent().proxy.layoutChanged.connect(self.populate_list)
        self.populate_list(initial=True)

    def populate_list(self, initial=False):
        self.list.clear()
        
        df = self.parent().df
        mask = self.parent().proxy.accepted_mask
        col = df.columns[self.col_ndx]
        full_col = df[col]
        disp_col = df.loc[mask, col]
        
        def _build_item(val, state=None) -> QListWidgetItem:
            item = QListWidgetItem(str(val))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if state is None:
                if val in disp_col.values:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
            item.setCheckState(state)
            return item

        # Add a (Select All)
        if mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        self._action_select_all = _build_item(
            '(Select All)', state=select_all_state)
        self.list.addItem(self._action_select_all)

        # Add filter items
        if initial:
            unq_list = full_col.unique()
        else:
            unq_list = disp_col.unique()
            
        try:
            unq_list = np.sort(unq_list)
        except:
            pass
        
        for val in unq_list:
            self.list.addItem(_build_item(val))

    def on_listitem_changed(self, item: QListWidgetItem):

        self.list.blockSignals(True)
        if item is self._action_select_all:
            # Handle "select all" item click
            state = item.checkState()

            # Select/deselect all items
            for i in range(self.list.count()):
                if i is self._action_select_all:
                    continue
                itm = self.list.item(i)
                itm.setCheckState(state)
        else:
            # Non "select all" item; figure out what "select all" should be
            if item.checkState() == Qt.Unchecked:
                self._action_select_all.setCheckState(Qt.Unchecked)
            else:
                # "select all" only checked if all other items are checked
                for i in range(self.list.count()):
                    itm = self.list.item(i)
                    if itm is self._action_select_all:
                        continue
                    if itm.checkState() == Qt.Unchecked:
                        self._action_select_all.setCheckState(Qt.Unchecked)
                        break
                else:
                    self._action_select_all.setCheckState(Qt.Checked)
        self.list.blockSignals(False)

    def checked_values(self) -> List[str]:
        checked = []
        for i in range(self.list.count()):
            itm = self.list.item(i)
            if itm is self._action_select_all:
                continue
            if itm.checkState() == Qt.Checked:
                checked.append(itm.text())
        return checked

    def apply_and_close(self):
        self.parent().blockSignals(True)
        self.parent().proxy.list_filter(self.checked_values())
        self.parent().blockSignals(False)
        self.menu.close()

