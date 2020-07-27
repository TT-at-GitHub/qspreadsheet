import sys, os
import typing

import numpy as np
import pandas as pd
import operator

from fx import fx
from fx.deco import decorate_methods

import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from functools import partial


class DynamicFilterLineEdit(QLineEdit):
    """Filter textbox for a DataFrameTable"""

    def __init__(self, *args, **kwargs):
        self._always_dynamic = kwargs.pop('always_dynamic', False)

        super(DynamicFilterLineEdit, self).__init__(*args, **kwargs)

        self.col_to_filter = None
        self._host = None


    def bind_dataframe_view(self, host, col_ix):
        """Bind tihs DynamicFilterLineEdit to a DataFrameTable's column
        Args:
            host (DataFrameWidget)
                Host to filter
            col_ix (int)
                Index of column of host to filter
        """
        self.host = host
        self.col_to_filter = col_ix
        self.textChanged.connect(self._update_filter)

    @property
    def host(self):
        if self._host is None:
            raise RuntimeError("Must call bind_dataframe_view() "
            "before use.")
        else:
            return self._host

    @host.setter
    def host(self, value):
        if not isinstance(value, DataFrameView):
            raise ValueError("Must bind to a DataFrameView, not %s" % value)
        else:
            self._host = value

        if not self._always_dynamic:
            self.editingFinished.connect(self._host._data_model.end_dynamic_filter)


    def focusInEvent(self, QFocusEvent):
        self._host._data_model.beginDynamicFilter()


    def _update_filter(self, text):
        """Called everytime we type in the filter box"""
        col_ix = self.col_to_filter

        self.host.filter(col_ix, text)


class DynamicFilterMenuAction(QWidgetAction):
    """Filter textbox in column-header right-click menu"""

    def __init__(self, parent, menu, col_ix):
        """Filter textbox in column right-click menu
            Args:
                parent (DataFrameWidget)
                    Parent who owns the DataFrame to filter
                menu (QMenu)
                    Menu object I am located on
                col_ix (int)
                    Index of column used in pandas DataFrame we are to filter
        """
        super(DynamicFilterMenuAction, self).__init__(parent)

        # State
        self.parent_menu = menu

        # Build Widgets
        widget = QWidget()
        layout = QHBoxLayout()
        self.label = QLabel('Filter')
        self.text_box = DynamicFilterLineEdit()
        self.text_box.bind_dataframe_view(self.parent(), col_ix)
        self.text_box.returnPressed.connect(self._close_menu)

        layout.addWidget(self.label)
        layout.addWidget(self.text_box)
        widget.setLayout(layout)

        self.setDefaultWidget(widget)


    def _close_menu(self):
        """Gracefully handle menu"""
        self.parent_menu.close()


class FilterListMenuWidget(QWidgetAction):
    """Filter textbox in column-right click menu"""

    def __init__(self, parent, menu, col_ix):
        """Filter textbox in column right-click menu
        Args:
            parent (DataFrameWidget)
                Parent who owns the DataFrame to filter
            menu (QMenu)
                Menu object I am located on
            col_ix (int)
                Column index used in pandas DataFrame we are to filter
            label (str)
                Label in popup menu
        """
        super(FilterListMenuWidget, self).__init__(parent)

        # State
        self.menu = menu
        self.col_ix = col_ix

        # Build Widgets
        widget = QWidget()
        layout = QVBoxLayout()
        self.list = QListWidget()
        self.list.setFixedHeight(100)

        layout.addWidget(self.list)
        widget.setLayout(layout)

        self.setDefaultWidget(widget)

        # Signals/slots
        self.list.itemChanged.connect(self.on_listitem_changed)
        self.parent().dataframe_changed.connect(self._populate_list)

        self._populate_list(inital=True)


    def _populate_list(self, inital=False):
        self.list.clear()

        df = self.parent()._data_model._original_df
        col = df.columns[self.col_ix]
        full_col = set(df[col])  # All Entries possible in this column
        disp_col = set(self.parent().get_df()[col]) # Entries currently displayed


        def _build_item(val, state=None):
            item = QListWidgetItem('%s' % val)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if state is None:
                if val in disp_col:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
            item.setCheckState(state)
            item.checkState()
            self.list.addItem(item)
            return item

        # Add a (Select All)
        if full_col == disp_col:
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked
        self._action_select_all = _build_item('(Select All)', state=select_all_state)

        # Add filter items
        if inital:
            build_list = full_col
        else:
            build_list = disp_col
        for val in sorted(build_list):
            _build_item(val)

        # Add a (Blanks)
        # TODO


    def on_listitem_changed(self, item):
        ###
        # Figure out what "select all" check-box state should be
        ###
        self.list.blockSignals(True)
        if item is self._action_select_all:
            # Handle "select all" item click
            if item.checkState() == Qt.Checked:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            # Select/deselect all items
            for i in range(self.list.count()):
                if i is self._action_select_all: 
                    continue
                i = self.list.item(i)
                i.setCheckState(state)
        else:
            # Non "select all" item; figure out what "select all" should be
            if item.checkState() == Qt.Unchecked:
                self._action_select_all.setCheckState(Qt.Unchecked)
            else:
                # "select all" only checked if all other items are checked
                for i in range(self.list.count()):
                    i = self.list.item(i)
                    if i is self._action_select_all: 
                        continue
                    if i.checkState() == Qt.Unchecked:
                        self._action_select_all.setCheckState(Qt.Unchecked)
                        break
                else:
                    self._action_select_all.setCheckState(Qt.Checked)
        self.list.blockSignals(False)

        ###
        # Filter dataframe according to list
        ###
        include = []
        for i in range(self.list.count()):
            i = self.list.item(i)
            if i is self._action_select_all: 
                continue
            if i.checkState() == Qt.Checked:
                include.append(str(i.text()))

        self.parent().blockSignals(True)
        self.parent().filter_values(self.col_ix, include)
        self.parent().blockSignals(False)
        # self.parent()._enable_widgeted_cells()


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
            font: bold 14px 'Consolas';
        ''')

        self.button.setFixedSize(QSize(25, 20))
        icon = QIcon((QPixmap("./images/next.svg")
                    .transformed(QTransform().rotate(90))))
        self.button.setIcon(icon)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2, Qt.AlignJustify)
        layout.addWidget(self.button, 0, 1, 1, 1, Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumHeight(30)


class HeaderItem():

    def __init__(self, widget: QWidget=None, margins: QMargins=None):
        self.widget = widget
        self.margins = margins

        if self.margins is None:
            self.margins = QMargins(2, 2, 2, 2)


class HeaderView(QHeaderView):

    def __init__(self, columns: list, parent=None):
        super().__init__(Qt.Horizontal, parent)

        self.headers = []
        
        # Header buttons Signals/Slots
        self.filter_btn_mapper = QSignalMapper(self)

        for i, name in enumerate(columns):
            header_widget = ColumnHeaderWidget(labelText=name, parent=self)
            header = HeaderItem(widget=header_widget)
            self.filter_btn_mapper.setMapping(header_widget.button, name)
            header_widget.button.clicked.connect(self.filter_btn_mapper.map)
            self.headers.append(header)

        self.filter_btn_mapper.mapped[str].connect(self.on_header_clicked)
        
        # Sections Signals/Slots
        self.sectionResized.connect(self.on_section_resized)
        self.sectionMoved.connect(self.on_section_moved)

        # StyleSheet
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


    def on_header_clicked(self, s: str):
        pass
        # btn = self.filter_btn_mapper.mapping(s)
        # print('Change the icon here!')


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

            header = self.headers[logical]
            self._set_item_geometry(header, logical)


    def _set_item_geometry(self, item: HeaderItem, logical:int):
        item.widget.setGeometry(
            self.sectionViewportPosition(logical), -4,
            self.sectionSize(logical) - item.margins.left() - item.margins.right(),
            self.height() + item.margins.top() + item.margins.bottom() + 5)


    def on_section_moved(self, logical, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            header = self.headers[i]

            self.headers[logical].w.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)


    def fix_item_positions(self):
        for i, header in enumerate(self.headers):
            self._set_item_geometry(header, i)


    def set_item_widget(self, index: int, widget: QWidget):
        widget.setParent(self)
        self.headers[index].w = widget
        self.headers[index].margins = QMargins(2, 2, 2, 2)
        self.fix_item_positions()
        widget.show()


    def set_item_margin(self, index: int, margins: QMargins):
        self.headers[index].margins = margins


class DataFrameItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(DataFrameItemDelegate, self).__init__(parent)


    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)


    def sizeHint(self, option, index):
        return QStyledItemDelegate.sizeHint(self, option, index)


    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            background-color:#fffd99
        """)
        editor.returnPressed.connect(self.commitAndCloseEditor)
        return editor
        # else:
        #     return QStyledItemDelegate.createEditor(self, parent, option, index)


    def commitAndCloseEditor(self):
        editor = self.sender()
        # if isinstance(editor, (QTextEdit, QLineEdit)):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole)
        editor.setText(text)
        # else:
            # QStyledItemDelegate.setEditorData(self, editor, index)


    def setModelData(self, editor, model, index):
        QStyledItemDelegate.setModelData(self, editor, model, index)


class DataFrameModel(QAbstractTableModel):

    def __init__(self, header_model: HeaderView, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self._df = pd.DataFrame()
        self._original_df = pd.DataFrame()
        self._pre_dyn_filter_df = None
        self._resort = lambda : None # Null resort functon

        self.logical = None
        self.dirty = False

        self._header_model = header_model
        self.filter_values_mapper = QSignalMapper(self)


    def set_df(self, df: pd.DataFrame):
        self._original_df = df.copy()
        self._pre_dyn_filter_df = None

        self.modelAboutToBeReset.emit()
        self._df = df
        self.modelReset.emit()


    def get_df(self) -> pd.DataFrame:
        return self._df


    def rowCount(self, parent: QModelIndex) -> int:
        return self._df.index.size


    def columnCount(self, parent: QModelIndex) -> int:
        return self._df.columns.size


    def data(self, index: QModelIndex, role: int) -> typing.Any:
        if role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])

        return None


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)


    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self._df.shape[0]:
            if not value:
                self._df.iloc[index.row(), index.column()] = np.nan
            else:
                try:
                    number = pd.to_numeric(value)
                except :
                    self._df.iloc[index.row(), index.column()] = str(value)
                else:
                    self._df.iloc[index.row(), index.column()] = number

            self.dirty = True

            self.dataChanged.emit(index, index)
            return True
        return False


    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Any:
        if section < 0:
            print('section: {}'.format(section))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header_model.headers[section]
            if orientation == Qt.Vertical:
                return str(self._df.index[section])

        return None


    def on_horizontal_scroll(self, dx: int):
        self._header_model.fix_item_positions()


    def on_vertical_scroll(self, dy: int):
        pass


    def on_action_all_triggered(self, dx: int):
        self.logical

    @Slot()
    def begin_dynamic_filter(self):
        """Effects of using the "filter" function will not become permanent until endDynamicFilter called"""
        if self._pre_dyn_filter_df is None:
            print( "NEW DYNAMIC FILTER MODEL")
            self._pre_dyn_filter_df = df.copy()
        else:
            # Already dynamically filtering, so don't override that
            print( "SAME DYNAMIC FILTER MODEL")
            pass

    @Slot()
    def end_dynamic_filter(self):
        """Makes permanent the effects of the dynamic filter"""
        print( " * * * RESETING DYNAMIC")
        self._pre_dyn_filter_df = None


    def sort(self, col_ix, order = Qt.AscendingOrder):
        df = self.get_df()

        if col_ix >= df.shape[1]:
            # Column out of bounds
            return

        self.layoutAboutToBeChanged.emit()
        ascending = True if order == Qt.AscendingOrder else False
        df = df.sort_values(by=df.columns[col_ix], ascending=ascending)

        self.layoutChanged.emit()

        # Set sorter to current sort (for future filtering)
        self._resort = partial(self.sort, col_ix, order)


    def reset(self):
        self.set_df(self._original_df.copy())
        self._resort = lambda: None
        self._pre_dyn_filter_df = None


    def filter_values(self, col_ix, include):
        df = self._original_df
        col = self.get_df().columns[col_ix]

        # Convert to string
        s_col = df[col].astype('str')

        # Filter
        self.set_df(df[s_col.isin(include)])

        # Resort
        self._resort()


    def filter_function(self, col_ix, function):
        df = self.get_df()
        col = df.columns[col_ix]

        self.set_df(df[function(df[col])])

        # Resort
        self._resort()


class DataFrameView(QTableView):

    dataframe_changed = Signal()
    cell_clicked = Signal(int, int)

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)

        # Set the views
        self._header_model = HeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self._header_model)
        self._header_model.filter_btn_mapper.mapped[str].connect(self.header_menu)
        
        self._data_model = DataFrameModel(self._header_model, self)
        # if df is None:
        #     df = pd.DataFrame()
        self._data_model.set_df(df)
        self.setModel(self._data_model)

        # Signals/Slots
        self._data_model.modelReset.connect(self.dataframe_changed)
        self._data_model.dataChanged.connect(self.dataframe_changed)
        self.clicked.connect(self.on_click)

        self.horizontalScrollBar().valueChanged.connect(self._data_model.on_horizontal_scroll)
        self.horizontalScrollBar().valueChanged.connect(self._data_model.on_vertical_scroll)

        item_delegate = DataFrameItemDelegate()
        self.setItemDelegate(item_delegate)

        # Create header menu bindings
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.header_menu)


    def make_cell_context_menu(self, menu, row_ix, col_ix):
        """Create the mneu displayed when right-clicking on a cell.
        Overrite this method to add custom right-click options

        Parameters
        ----------
            menu (QMenu)
                Menu to which to add actions
            row_ix (int)
                Row location in dataframe
            col_ix (int)
                Coloumn location in dataframe

        Returns
        -------
            menu (QMenu)
                Same menu passed in, with added actions
        """
        df = self._data_model.get_df()
        cell_val = df.iat[row_ix, col_ix]

        # By Value Filter
        def _cell_filter(s_col):
            return s_col == cell_val

        menu.addAction(self._qicon('CommandLink'),
            "By Value", 
            partial(self._data_model.filter_function, 
                    col_ix=col_ix, function=_cell_filter))

        # GreaterThan/LessThan filter
        def _cmp_filter(s_col, op):
            return op(s_col, cell_val)

        menu.addAction("Greater Than",
                        partial(self._data_model.filter_function, col_ix=col_ix,
                                function=partial(_cmp_filter, op=operator.ge)))
        menu.addAction("Less Than",
                        partial(self._data_model.filter_function, col_ix=col_ix,
                                function=partial(_cmp_filter, op=operator.le)))
        menu.addAction(self._qicon('DialogResetButton'),
                        "Clear",
                        self._data_model.reset)
        menu.addSeparator()

        # Save to Excel
        def _to_excel():
            from subprocess import Popen
            xlfile = "temp.xls"
            xlsheet = "Output"        

            df.to_excel(xlfile, xlsheet)
            Popen(xlfile, shell=True)

        menu.addAction("Open in Excel", _to_excel)

        return menu


    def contextMenuEvent(self, event):
        """Implements right-clicking on cell.

            NOTE: You probably want to overrite make_cell_context_menu, not this
            function, when subclassing.
        """
        row_ix = self.rowAt(event.y())
        col_ix = self.columnAt(event.x())

        if row_ix < 0 or col_ix < 0:
            return #out of bounds

        menu = QMenu(self)
        menu = self.make_cell_context_menu(menu, row_ix, col_ix)
        menu.exec_(self.mapToGlobal(event.pos()))


    def header_menu(self, name):
        """Create popup menu used for header"""
        
        menu = QMenu(self)

        pos = df.columns.get_loc(name)
        col_ix = self.horizontalHeader().logicalIndex(pos)

        if col_ix == -1:
            # Out of bounds
            return

        # Filter Menu Action
        menu.addAction(DynamicFilterMenuAction(self, menu, col_ix))
        menu.addAction(FilterListMenuWidget(self, menu, col_ix))
        menu.addAction(self._qicon('DialogResetButton'),
                        "Reset",
                        self._data_model.reset)

        # Sort Ascending/Decending Menu Action
        menu.addAction(self._qicon('TitleBarShadeButton'),
                        "Sort Ascending",
                       partial(self._data_model.sort, col_ix=col_ix, order=Qt.AscendingOrder))
        menu.addAction(self._qicon('TitleBarUnshadeButton'),
                        "Sort Descending",
                       partial(self._data_model.sort, col_ix=col_ix, order=Qt.DescendingOrder))
        menu.addSeparator()

        # Hide
        menu.addAction("Hide", partial(self.hideColumn, col_ix))

        # Show (column to left and right)
        for i in (-1, 1):
            if self.isColumnHidden(col_ix+i):
                
                menu.addAction("Show %s" % name,
                                partial(self.showColumn, col_ix+i))
        
        menu.exec_(QCursor.pos())


    def set_df(self, df: pd.DataFrame):
        self._data_model.set_df(df)


    def get_df(self):
        return self._data_model.get_df()


    def filter_values(self, col_ix, include):
        return self._data_model.filter_values(col_ix, include)


    def on_click(self, index: QModelIndex):
        if index.isValid():
            self.cell_clicked.emit(index.row(), index.column())


    def _qicon(self, icon_name):
        """Convinence function to get standard icons from Qt"""
        if not icon_name.startswith('SP_'):
            icon_name = 'SP_' + icon_name
        icon = getattr(QStyle, icon_name, None)
        if icon is None:
            raise Exception("Unknown icon %s" % icon_name)
        return self.style().standardIcon(icon)


class MainWindow(QMainWindow):
    
    MARGIN = 35

    def __init__(self, df: pd.DataFrame, title='Main Window'):
        super().__init__()

        self.title = title
        self.setWindowTitle(self.title)

        # Set the table and the data
        self.table = DataFrameView(df, self)
        self.setCentralWidget(self.table)

        # Set window size
        col_width = sum([self.table.columnWidth(i) for i in range(df.shape[1])])
        col_width = min(col_width + MainWindow.MARGIN * 2, 1280)
        self.setGeometry(200, 300, col_width, 300)
        self.setMinimumSize(QSize(400, 300))


    def datatable_updated(self):
        df = self.table.get_df()
        star = '*' if self.table.dirty else ''
        title = self.title + f'{star} ({df.shape[0]}, {df.shape[1]})'
        self.setWindowTitle(title)


def mock_df() -> pd.DataFrame:
    area = pd.Series({0 : 423967, 1: 695662, 2: 141297, 3: 170312, 4: 149995})
    pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
    states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
    df = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
    df.area = df.area.astype(float)
    return df


if __name__ == "__main__":

    df = mock_df()
    app = QApplication(sys.argv)
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec_())