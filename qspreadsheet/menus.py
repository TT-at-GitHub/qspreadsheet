import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet.custom_widgets import LabeledLineEdit
from qspreadsheet import LEFT


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

    def __init__(self, parent, menu, col_ndx):
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
        unq_list = self.parent().proxy.unique_values()
        try:
            unq_list = sorted(unq_list)
        except:
            pass

        def _build_item(val, state=None) -> QListWidgetItem:
            item = QListWidgetItem(str(val))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if state is None:
                if val in unq_list:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
            item.setCheckState(state)
            self.list.addItem(item)
            return item

        # Add a (Select All)
        self._action_select_all = _build_item(
            '(Select All)', state=Qt.Unchecked)
        self.list.addItem(self._action_select_all)

        # Add filter items
        num_checked = 0
        for val in unq_list:
            item = _build_item(val)
            if item.checkState() == Qt.Checked:
                num_checked += 1

        state = Qt.Checked if num_checked == len(unq_list) else Qt.Unchecked
        self.list.blockSignals(True)
        self._action_select_all.setCheckState(state)
        self.list.blockSignals(False)

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

