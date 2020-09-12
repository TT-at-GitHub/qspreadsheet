import operator
import os
import sys
from copy import deepcopy
from functools import partial
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import resources_rc
from qspreadsheet import richtextlineedit
from qspreadsheet import delegates
from qspreadsheet import LEFT

class LabeledLineEdit(QWidget):

    def __init__(self, label_text='', position=LEFT,
                 parent=None):
        super(LabeledLineEdit, self).__init__(parent)
        self.label = QLabel(label_text, self)
        self.lineEdit = QLineEdit(self)
        self.label.setBuddy(self.lineEdit)
        layout = QBoxLayout(QBoxLayout.LeftToRight
                            if position == LEFT else QBoxLayout.TopToBottom)
        layout.addWidget(self.label)
        layout.addWidget(self.lineEdit)
        self.setLayout(layout)


class LabeledTextEdit(QWidget):

    def __init__(self, labelText="", position=LEFT,
                 parent=None):
        super(LabeledTextEdit, self).__init__(parent)
        self.label = QLabel(labelText, self)
        self.textEdit = QTextEdit(self)
        self.label.setBuddy(self.textEdit)
        layout = QBoxLayout(QBoxLayout.LeftToRight
                            if position == LEFT else QBoxLayout.TopToBottom)
        layout.addWidget(self.label)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)


class LineEditMenuAction(QWidgetAction):
    """Labeled Textbox in menu"""

    def __init__(self, parent, menu, label_text='', position=LEFT):
        super(LineEditMenuAction, self).__init__(parent)

        widget = LabeledLineEdit(label_text, position, parent=menu)
        self.returnPressed = widget.lineEdit.returnPressed
        self.textChanged = widget.lineEdit.textChanged
        self.setDefaultWidget(widget)


class ColumnHeaderWidget(QWidget):

    def __init__(self, labelText="", parent=None):
        super(ColumnHeaderWidget, self).__init__(parent)
        self.label = QLabel(labelText, parent)
        self.button = QPushButton('', parent)
        self.button.setIconSize(QSize(12, 12))
        self.label.setBuddy(self.button)
        self.label.setWordWrap(True)
        self.label.setStyleSheet('''
            color: white;
            font: bold 14px 'Consolas'; ''')

        self.button.setFixedSize(QSize(25, 20))
        icon = QIcon(":/down-arrow")
        self.button.setIcon(icon)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2, Qt.AlignJustify)
        layout.addWidget(self.button, 0, 1, 1, 1, Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumHeight(30)


class HeaderItem():

    def __init__(self, widget: QWidget = None, margins: QMargins = None):
        self.widget = widget
        self.margins = margins

        if self.margins is None:
            self.margins = QMargins(2, 2, 2, 2)


class CustomHeaderView(QHeaderView):

    def __init__(self, columns: list, parent=None):
        super(CustomHeaderView, self).__init__(Qt.Horizontal, parent)

        self.headers = []
        self.filter_btn_mapper = QSignalMapper(self)

        for name in columns:
            header_widget = ColumnHeaderWidget(labelText=name, parent=self)
            header = HeaderItem(widget=header_widget)
            self.filter_btn_mapper.setMapping(header_widget.button, name)
            header_widget.button.clicked.connect(self.filter_btn_mapper.map)
            self.headers.append(header)

        self.filter_btn_mapper.mapped[str].connect(self.filter_clicked)
        self.sectionResized.connect(self.on_section_resized)
        self.sectionMoved.connect(self.on_section_moved)
        self.setStyleSheet('''
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #5dade2, stop: 0.5 #3498db,
                                            stop: 0.6 #3498db, stop:1 #21618c);
                color: white;
                padding-top: 4px;
                padding-bottom: 4px;
                padding-left: 4px;
                padding-right: 4px;
                border: 1px solid #21618c;

            /*
                margin-left: 2px;
                margin-right: 2px;
            */
            }''')

    def filter_clicked(self, name: str):
        btn = self.filter_btn_mapper.mapping(name)

    def showEvent(self, e: QShowEvent):
        for i, header in enumerate(self.headers):
            header.widget.setParent(self)
            self._set_item_geometry(header, i)
            header.widget.show()

        super().showEvent(e)

    def sizeHint(self) -> QSize:
        # insert space for our filter row
        super_sz_h = super().sizeHint()
        return QSize(super_sz_h.width() + 5,
                     super_sz_h.height() + 5)

    def on_section_resized(self, i):
        for ndx in range(i, len(self.headers)):
            logical = self.logicalIndex(ndx)
            self._set_item_geometry(self.headers[logical], logical)

    def _set_item_geometry(self, item: HeaderItem, logical: int):
        item.widget.setGeometry(
            self.sectionViewportPosition(logical), 0,
            self.sectionSize(logical) - item.margins.left() -
            item.margins.right() - 1,
            self.height() + item.margins.top() + item.margins.bottom() - 1)

    def on_section_moved(self, logical, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            header = self.headers[i]

            self.headers[logical].widget.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() -
                header.margins.right() - 1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)

    def fix_item_positions(self):
        for i, header in enumerate(self.headers):
            self._set_item_geometry(header, i)

    def set_item_widget(self, index: int, widget: QWidget):
        widget.setParent(self)
        self.headers[index].widget = widget
        self.headers[index].margins = QMargins(2, 2, 2, 2)
        self.fix_item_positions()
        widget.show()

    def set_item_margin(self, index: int, margins: QMargins):
        self.headers[index].margins = margins


class GenericDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(GenericDelegate, self).__init__(parent)
        self.delegates = {}

    def insertColumnDelegate(self, column, delegate):
        delegate.setParent(self)
        self.delegates[column] = delegate

    def removeColumnDelegate(self, column):
        if column in self.delegates:
            del self.delegates[column]

    def paint(self, painter, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QStyledItemDelegate.createEditor(self, parent, option,
                                                    index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, index)


class IntegerColumnDelegate(QStyledItemDelegate):

    def __init__(self, minimum=0, maximum=100, parent=None):
        super(IntegerColumnDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        spinbox = QSpinBox(parent)
        spinbox.setRange(self.minimum, self.maximum)
        spinbox.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return spinbox

    def setEditorData(self, editor, index):
        value = int(index.model().data(index, Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        model.setData(index, editor.value())


class DateColumnDelegate(QStyledItemDelegate):

    def __init__(self, minimum=QDate(),
                 maximum=QDate.currentDate(),
                 format="yyyy-MM-dd", parent=None):
        super(DateColumnDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.format = format

    def createEditor(self, parent, option, index):
        dateedit = QDateEdit(parent)
        dateedit.setDateRange(self.minimum, self.maximum)
        dateedit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dateedit.setDisplayFormat(self.format)
        dateedit.setCalendarPopup(True)
        return dateedit

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setDate(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date())


class PlainTextColumnDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(PlainTextColumnDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        lineedit = QLineEdit(parent)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())


class RichTextColumnDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(RichTextColumnDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        text = index.model().data(index, Qt.DisplayRole)
        palette = QApplication.palette()
        document = QTextDocument()
        document.setDefaultFont(option.font)
        if option.state & QStyle.State_Selected:
            document.setHtml("<font color={}>{}</font>".format(
                palette.highlightedText().color().name(), text))
        else:
            document.setHtml(text)
        painter.save()
        color = (palette.highlight().color()
                 if option.state & QStyle.State_Selected
                 else QColor(index.model().data(index,
                                                Qt.BackgroundColorRole)))
        painter.fillRect(option.rect, color)
        painter.translate(option.rect.x(), option.rect.y())
        document.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        text = index.model().data(index)
        document = QTextDocument()
        document.setDefaultFont(option.font)
        document.setHtml(text)
        return QSize(document.idealWidth() + 5,
                     option.fontMetrics.height())

    def createEditor(self, parent, option, index):
        lineedit = richtextlineedit.RichTextLineEdit(parent)
        return lineedit

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setHtml(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.toSimpleHtml())


class DefaultDataFrameDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(DefaultDataFrameDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        return QStyledItemDelegate.sizeHint(self, option, index)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            background-color: #fffd99
        """)
        editor.returnPressed.connect(self.commitAndCloseEditor)
        return editor

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole)
        editor.setText(text)

    def setModelData(self, editor, model, index):
        QStyledItemDelegate.setModelData(self, editor, model, index)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, df: pd.DataFrame, header_model: CustomHeaderView, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.df = df.copy()
        self._header_model = header_model
        self._header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)
        self.filter_values_mapper = QSignalMapper(self)
        self.logical = None
        self.dirty = False

    def rowCount(self, parent: QModelIndex) -> int:
        return self.df.shape[0]

    def columnCount(self, parent: QModelIndex) -> int:
        return self.df.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            return str(self.df.iat[index.row(), index.column()])

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                            Qt.ItemIsEditable)

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self.rowCount(index):
            if not value:
                self.df.iloc[index.row(), index.column()] = np.nan
            else:
                try:
                    number = pd.to_numeric(value)
                except:
                    self.df.iloc[index.row(), index.column()] = str(value)
                else:
                    self.df.iloc[index.row(), index.column()] = number

            self.dirty = True

            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if section < 0:
            print('section: {}'.format(section))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header_model.headers[section]
            if orientation == Qt.Vertical:
                return str(self.df.index[section])

        return None

    def on_horizontal_scroll(self, dx: int):
        self._header_model.fix_item_positions()

    def on_vertical_scroll(self, dy: int):
        pass

    def on_action_all_triggered(self, dx: int):
        self.logical

    def filter_clicked(self, name):
        pass


class ActionButtonBox(QWidgetAction):

    def __init__(self, parent):
        super(ActionButtonBox, self).__init__(parent)

        btn_box = QDialogButtonBox(parent)
        btn_box.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.accepted = btn_box.accepted
        self.rejected = btn_box.rejected
        self.setDefaultWidget(btn_box)


class FilterListMenuWidget(QWidgetAction):
    """Checkboxed list filter menu"""

    def __init__(self, parent, menu, col_ndx):
        """Checkbox list filter menu
        Args:
            parent (Widget)
                Parent
            menu (QMenu)
                Menu object this list is located on
            col_ndx (int)
                Column index to filter
            label (str)
                Label in popup menu
        """
        super(FilterListMenuWidget, self).__init__(parent)

        # State
        self.menu = menu

        # Build Widgets
        widget = QWidget()
        layout = QVBoxLayout()
        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListView::item:selected {
                background: rgb(195, 225, 250);
                color: rgb(0, 0, 0);
            } """)
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


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent=None) -> None:
        super(DataFrameSortFilterProxy, self).__init__(parent)
        self._df = pd.DataFrame()
        self.accepted_mask = pd.Series()
        self._masks_cache = []

    def set_df(self, df: pd.DataFrame):
        self._df = df
        self.accepted_mask = self._alltrues()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        return self.accepted_mask.iloc[source_row]

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


class DataFrameView(QTableView):

    def __init__(self, df: pd.DataFrame, delegate: Optional[QStyledItemDelegate] = None, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)

        self.header_model = CustomHeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self.header_model)

        self.model = DataFrameModel(
            df=df, header_model=self.header_model, parent=self)
        self.header_model.filter_btn_mapper.mapped[str].connect(
            self.filter_clicked)

        self.proxy = DataFrameSortFilterProxy(self)
        self.proxy.set_df(df)
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self.model.on_horizontal_scroll)
        self.verticalScrollBar().valueChanged.connect(self.model.on_vertical_scroll)

        # TODO: make the delegate generic !
        self.delegate = delegate or DefaultDataFrameDelegate(self)
        self.setItemDelegate(self.delegate)

    @property
    def df(self) -> pd.DataFrame:
        return self.model.df

    @df.setter
    def df(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise TypeError('Invalid type for `df`. Expected DataFrame')
        self.model.df = df

    def filter_clicked(self, name: str):
        btn = self.header_model.filter_btn_mapper.mapping(name)

        col_ndx = self.df.columns.get_loc(name)
        self.proxy.setFilterKeyColumn(col_ndx)

        # TODO: look for other ways to position the menu
        header_pos = self.mapToGlobal(btn.parent().pos())
        menu = self.make_header_menu(col_ndx)
        menu_pos = QPoint(header_pos.x() + menu.width() - btn.width() + 5,
                          header_pos.y() + btn.height() + 15)
        menu.exec_(menu_pos)

    def make_cell_context_menu(self, row_ndx: int, col_ndx: int) -> QMenu:
        menu = QMenu(self)
        cell_val = self.df.iat[row_ndx, col_ndx]

        # By Value Filter
        def _quick_filter(cell_val):
            self.proxy.setFilterKeyColumn(col_ndx)
            self.proxy.string_filter(str(cell_val))

        menu.addAction(self._icon('CommandLink'),
                       "Filter By Value", partial(_quick_filter, cell_val))

        # GreaterThan/LessThan filter
        def _cmp_filter(s_col, op):
            return op(s_col, cell_val)
        # menu.addAction("Filter Greater Than",
        #                 partial(self._data_model.filterFunction, col_ndx=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.ge)))
        # menu.addAction("Filter Less Than",
        #                 partial(self._data_model.filterFunction, col_ndx=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.le)))
        menu.addAction(self._icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)
        menu.addSeparator()

        # Open in Excel
        menu.addAction("Open in Excel...", self._to_excel)

        return menu

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Implements right-clicking on cell.

            NOTE: You probably want to overrite make_cell_context_menu, not this
            function, when subclassing.
        """
        row_ndx = self.rowAt(event.y())
        col_ndx = self.columnAt(event.x())

        if row_ndx < 0 or col_ndx < 0:
            return  # out of bounds

        menu = self.make_cell_context_menu(row_ndx, col_ndx)
        menu.exec_(self.mapToGlobal(event.pos()))

    def make_header_menu(self, col_ndx: int) -> QMenu:
        """Create popup menu used for header"""

        menu = QMenu(self)

        # Filter Menu Action
        str_filter = LineEditMenuAction(self, menu, 'Filter')
        str_filter.returnPressed.connect(menu.close)
        str_filter.textChanged.connect(self.proxy.string_filter)
        menu.addAction(str_filter)

        list_filter = FilterListMenuWidget(self, menu, col_ndx)
        menu.addAction(list_filter)
        menu.addAction(self._icon('DialogResetButton'),
                       "Clear Filter",
                       self.proxy.reset_filter)

        # Sort Ascending/Decending Menu Action
        menu.addAction(self._icon('TitleBarShadeButton'),
                       "Sort Ascending",
                       partial(self.proxy.sort, col_ndx, Qt.AscendingOrder))
        menu.addAction(self._icon('TitleBarUnshadeButton'),
                       "Sort Descending",
                       partial(self.proxy.sort, col_ndx, Qt.DescendingOrder))

        menu.addSeparator()

        # Hide
        menu.addAction("Hide Column", partial(self.hideColumn, col_ndx))

        # Unhide column to left and right
        for i in (-1, 1):
            ndx = col_ndx + i
            if self.isColumnHidden(ndx):
                menu.addAction(f'Unhide {self.df.columns[ndx]}',
                               partial(self.showColumn, ndx))

        # Unhide all hidden columns
        def _unhide_all(hidden_indices: list):
            for ndx in hidden_indices:
                self.showColumn(ndx)
        hidden_indices = self._get_hidden_column_indices()
        if hidden_indices:
            menu.addAction(f'Unhide All',
                           partial(_unhide_all, hidden_indices))

        menu.addSeparator()

        # Filter Button box
        action_btn_box = ActionButtonBox(menu)
        action_btn_box.accepted.connect(list_filter.apply_and_close)
        action_btn_box.rejected.connect(menu.close)
        menu.addAction(action_btn_box)

        return menu

    def _to_excel(self):
        from subprocess import Popen
        rows = self.proxy.accepted_mask
        columns = self._get_visible_column_names()
        fname = 'temp.xlsx'
        self.df.loc[rows, columns].to_excel(fname, 'Output')
        Popen(fname, shell=True)

    def _get_visible_column_names(self) -> list:
        return [self.df.columns[ndx] for ndx in range(self.df.shape[1]) if not self.isColumnHidden(ndx)]

    def _get_hidden_column_indices(self) -> list:
        return [ndx for ndx in range(self.df.shape[1]) if self.isColumnHidden(ndx)]

    def _icon(self, icon_name: str) -> QIcon:
        """Convenience function to get standard icons from Qt"""
        if not icon_name.startswith('SP_'):
            icon_name = 'SP_' + icon_name
        icon = getattr(QStyle, icon_name, None)
        if icon is None:
            raise Exception("Unknown icon {}".format(icon_name))
        return self.style().standardIcon(icon)


class MainWindow(QMainWindow):

    def __init__(self, df: pd.DataFrame, delegate: Optional[QStyledItemDelegate] = None):
        super().__init__()

        self.table_view = DataFrameView(df=df, parent=self)
        delegate = delegate or delegates.GenericDelegate(self)
        self.table_view.setItemDelegate(delegate)
        central_widget = QWidget(self)
        h_layout = QHBoxLayout()
        central_widget.setLayout(h_layout)
        h_layout.addWidget(self.table_view)

        self.setCentralWidget(central_widget)
        self.setMinimumSize(QSize(960, 640))
        self.setWindowTitle("Table View")

