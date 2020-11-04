import logging
import os
import sys
from typing import List, Tuple

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet.common import LEFT, SER, standard_icon
from qspreadsheet.custom_widgets import LabeledLineEdit
from qspreadsheet.dataframe_model import DataFrameModel
from qspreadsheet.worker import Worker

logger = logging.getLogger(__name__)

 
class LineEditMenuAction(QWidgetAction):
    """Labeled Textbox in menu"""

    def __init__(self, parent, menu, label_text='', position=LEFT):
        super(LineEditMenuAction, self).__init__(parent)

        widget = LabeledLineEdit(label_text, position, parent=menu)
        self.returnPressed = widget.lineEdit.returnPressed
        self.textChanged = widget.lineEdit.textChanged
        self.setDefaultWidget(widget)


class FilterListMenuWidget(QWidgetAction):
    """Checkboxed list filter menu"""

    def __init__(self, parent=None) -> None:
        """Checkbox list filter menu

            Arguments
            ----------
            
            parent: (Widget)
                Parent
            
            menu: (QMenu)
                Menu object this list is located on
        """
        super(FilterListMenuWidget, self).__init__(parent)

        # Build Widgets
        widget = QWidget()
        layout = QVBoxLayout()
        self.list = QListWidget()
        
        self.list.setStyleSheet("""
            QListView::item:selected {
                background: rgb(195, 225, 250);
                color: rgb(0, 0, 0);
            } """)
        self.list.setFixedHeight(150)
        self.list.setLayoutMode(QListView.LayoutMode.Batched)
        self.list.setUniformItemSizes(True)

        layout.addWidget(self.list)

        # This button in made visible if the number 
        # of items to show is more than the initial limit
        btn = QPushButton('Not all items showing')
        
        btn.setIcon(standard_icon('MessageBoxWarning'))
        btn.setVisible(False)
        layout.addWidget(btn)
        self.show_all_btn = btn

        widget.setLayout(layout)
        self.setDefaultWidget(widget)

        # Signals/slots
        self.list.itemChanged.connect(self.on_listitem_changed)

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
        self.list.scrollToItem(item)
        self.list.blockSignals(False)

    def values(self) -> Tuple[List[str], bool]:
        checked = []
        select_all = False
        for i in range(self.list.count()):
            itm = self.list.item(i)
            if itm is self._action_select_all:
                select_all = (itm.checkState() == Qt.Checked)
                if select_all:
                    break
                else:
                    continue
            if itm.checkState() == Qt.Checked:
                checked.append(itm.text())
        return checked, select_all