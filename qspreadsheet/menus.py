import logging
import os
import sys
from typing import List, Optional, Tuple

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet.common import LEFT, SER, standard_icon
from qspreadsheet.custom_widgets import LabeledLineEdit
from qspreadsheet.dataframe_model import DataFrameModel
from qspreadsheet.worker import Worker

logger = logging.getLogger(__name__)

 
class LineEditWidgetAction(QWidgetAction):
    """Labeled Textbox in menu"""

    def __init__(self, parent, menu, label_text='', position=LEFT):
        super(LineEditWidgetAction, self).__init__(parent)

        widget = LabeledLineEdit(label_text, position, parent=menu)
        self.returnPressed = widget.lineEdit.returnPressed
        self.textChanged = widget.lineEdit.textChanged
        self.setDefaultWidget(widget)


class FilterListWidgetAction(QWidgetAction):
    """Checkboxed list filter menu"""

    select_all_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        """Checkbox list filter menu

            Arguments
            ----------
            
            parent: (Widget)
                Parent
            
            menu: (QMenu)
                Menu object this list is located on
        """
        super(FilterListWidgetAction, self).__init__(parent)

        # Build Widgets
        widget = QWidget()
        layout = QVBoxLayout()
        self.list = QListWidget(widget)
        self.list.setStyleSheet("""
            QListView::item:selected {
                background: rgb(195, 225, 250);
                color: rgb(0, 0, 0);
            } """)
        self.list.setMinimumHeight(150)
        self.list.setUniformItemSizes(True)

        layout.addWidget(self.list)

        # This button in made visible if the number 
        # of items to show is more than the initial limit
        btn = QPushButton('Not all items showing')
        
        btn.setIcon(standard_icon('MessageBoxWarning'))
        btn.setVisible(False)
        layout.addWidget(btn)
        self.show_all_btn = btn
        self.select_all_item: Optional[QListWidgetItem] = None

        widget.setLayout(layout)
        self.setDefaultWidget(widget)

        # Signals/slots
        self.list.itemChanged.connect(self.on_listitem_changed)
        self.num_checked = 0
        
    def addItem(self, item: QListWidgetItem):
        if item.checkState() == Qt.Checked:
            self.num_checked += 1
        else:
            self.num_checked -= 1
        assert(self.num_checked >= 0)

        self.list.addItem(item)

    def addSelectAllItem(self, item: QListWidgetItem):
        self.select_all_item = item
        self.list.addItem(item)

    def clear(self):
        self.list.clear()
        self.num_checked = 0

    def on_listitem_changed(self, item: QListWidgetItem):

        self.list.blockSignals(True)
        if item is self.select_all_item:
            # Handle "select all" item click
            state = item.checkState()
            # Select/deselect all items
            for i in range(self.list.count()):
                itm = self.list.item(i)
                if itm is self.select_all_item:
                    continue
                itm.setCheckState(state)
            
            all_checked = (state == Qt.Checked)
            # -1 is for the select_all_item
            self.num_checked =  self.list.count() - 1 if all_checked else 0
            self.select_all_changed.emit(all_checked)
        else:
            # Non "select all" item; figure out what "select all" should be
            if item.checkState() == Qt.Unchecked:
                self.num_checked -= 1
            else:
                self.num_checked += 1
            assert(self.num_checked >= 0)
            
            self.on_item_updated()

            state = Qt.Checked if self.num_checked > 0 else Qt.Unchecked
            self.select_all_item.setCheckState(state)

                # # "select all" only checked if all other items are checked
                # for i in range(self.list.count()):
                #     itm = self.list.item(i)
                #     if itm is self.select_all_item:
                #         continue
                #     if itm.checkState() == Qt.Unchecked:
                #         self.select_all_item.setCheckState(Qt.Unchecked)
                #         # self.select_all_changed.emit(False)
                #         break
                # else:
                #     self.select_all_item.setCheckState(Qt.Checked)
                #     self.select_all_changed.emit(True)

        self.list.scrollToItem(item)
        self.list.blockSignals(False)

    def values(self) -> List[str]:
        checked = []
        for i in range(self.list.count()):
            itm = self.list.item(i)
            if itm is self.select_all_item:
                continue
            if itm.checkState() == Qt.Checked:
                checked.append(itm.text())
        return checked

    def on_item_updated(self):
        if self.num_checked == 0:
            self.select_all_changed.emit(False)
        elif self.num_checked == 1:
            self.select_all_changed.emit(True)
