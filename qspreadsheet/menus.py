import logging
import os
import sys
import traceback
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

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

    INITIAL_LIMIT = 5000

    def __init__(self, parent, model: DataFrameModel, column_index: int) -> None:
        """Checkbox list filter menu

            Arguments
            ----------
            
            parent: (Widget)
                Parent
            
            menu: (QMenu)
                Menu object this list is located on
        """
        super(FilterListMenuWidget, self).__init__(parent)
        self._model = model
        self.column_index = column_index
                
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
        
        btn.clicked.connect(self._refill_list)
        btn.setIcon(standard_icon('MessageBoxWarning'))
        btn.setVisible(False)
        layout.addWidget(btn)
        self.btn_show_all = btn

        widget.setLayout(layout)
        self.setDefaultWidget(widget)

        # Signals/slots
        self.list.itemChanged.connect(self.on_listitem_changed)


    def _refill_list(self):
        worker = Worker(func=self.add_list_items, 
            values=self.unique.iloc[self.INITIAL_LIMIT :], 
            column_index=self.column_index,
            mask=self.mask)
        worker.signals.error.connect(self.on_error)
        worker.signals.result.connect(lambda: self.btn_show_all.setVisible(False))
        worker.signals.about_to_start.connect(lambda: self.btn_show_all.setEnabled(False))
        worker.signals.finished.connect(lambda: self.btn_show_all.setEnabled(True))

        tp = QThreadPool(self)
        # worker.run()
        tp.start(worker)

    def on_error(self, exc_info: Tuple):
        logger.error(msg='ERROR.', exc_info=exc_info)
        formatted = ' '.join(traceback.format_exception(*exc_info, limit=4))
        QMessageBox.critical(self, 'ERROR.', formatted, QMessageBox.Ok)
    
    def populate_list(self):
        self.list.clear()

        self.unique, self.mask = self._model.get_filter_values_for(self.column_index)

        # Add a (Select All)
        if self.mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        item = QListWidgetItem('(Select All)')
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(select_all_state)
        self.list.addItem(item)
        self._action_select_all = item

        if self.unique.size > self.INITIAL_LIMIT:            
            sliced_unique = self.unique.iloc[ : self.INITIAL_LIMIT]
            self.add_list_items(sliced_unique)
            self.btn_show_all.setVisible(True)
        else:
            self.add_list_items(self.unique)


    def add_list_items(self, values: SER, **kwargs):
        """
            values : {pd.Series}: values to add to the list
            
            mask : {pd.Series}: bool mask showing if item is visible
            
            **kwargs : {dict}: to hold the `progress_callback` from Worker
        """

        for row_ndx, val in values.items():
            
            index = self._model.createIndex(row_ndx, self.column_index)
            value = self._model.delegate.display_data(index, val)
            state = Qt.Checked if self.mask.iloc[row_ndx] else Qt.Unchecked
            
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(state)
            self.list.addItem(item)
            
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
