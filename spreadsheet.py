import sys, os
from functools import partial
import operator

import numpy as np
import pandas as pd

import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from header import CustomHeaderView
from table import DataFrameModel, DataFrameDelegate
from labelledwidgets import LineEditMenuAction


class FilterListMenuWidget(QWidgetAction):
    """Checkbox list filter menu"""

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
        self.col_ndx = col_ndx
        self.checked_values = []

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
        self.parent().proxy.layoutChanged.connect(self.populate_list)

        self.populate_list(initial=True)


    def populate_list(self, initial=False):
        self.list.clear()
        self.checked_values.clear()

        df = self.parent().df
        mask = self.parent().proxy.accepted_mask
        col = df.columns[self.col_ndx]
        full_col = df[col]  # All Entries possible in this column
        disp_col = df.loc[mask, col] # Entries currently displayed

        def _build_item(val, state=None) -> QListWidgetItem:
            item = QListWidgetItem(str(val))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if state is None:
                if val in disp_col.values:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
            item.setCheckState(state)
            item.checkState()
            return item

        # Add a (Select All)
        if mask.all():
            select_all_state = Qt.Checked
        else:
            select_all_state = Qt.Unchecked

        self._action_select_all = _build_item('(Select All)', state=select_all_state)
        self.list.addItem(self._action_select_all)

        # Add filter items
        if initial:
            build_list = full_col.unique()
        else:
            build_list = disp_col.unique()
            
        # build_list = fx.sort_mix_values(pandas.Series(data=list(build_list))).to_list()
        for val in np.sort(build_list):
            self.list.addItem( _build_item(val))


    def on_listitem_changed(self, item):

        self.list.blockSignals(True)
        if item is self._action_select_all:
            # Handle "select all" item click
            state = item.checkState()

            # Select/deselect all items
            for i in range(self.list.count()):
                if i is self._action_select_all: 
                    continue
                item = self.list.item(i)
                item.setCheckState(state)
        else:
            # Non "select all" item; figure out what "select all" should be
            if item.checkState() == Qt.Unchecked:
                self._action_select_all.setCheckState(Qt.Unchecked)
            else:
                # "select all" only checked if all other items are checked
                for i in range(self.list.count()):
                    item = self.list.item(i)
                    if item is self._action_select_all: 
                        continue
                    if item.checkState() == Qt.Unchecked:
                        self._action_select_all.setCheckState(Qt.Unchecked)
                        break
                else:
                    self._action_select_all.setCheckState(Qt.Checked)
        self.list.blockSignals(False)

        for i in range(self.list.count()):
            item = self.list.item(i)
            if item is self._action_select_all:
                continue
            if item.checkState() == Qt.Checked:
                self.checked_values.append(item.text())


    def apply_and_close(self):
        self.parent().blockSignals(True)
        self.parent().proxy.setFilterKeyColumn(self.col_ndx)
        self.parent().proxy.isin_filter(self.checked_values)
        self.checked_values.clear()
        self.parent().blockSignals(False)
        self.menu.close()


class DataFrameSortFilterProxy(QSortFilterProxyModel):

    def __init__(self) -> None:
        super(DataFrameSortFilterProxy, self).__init__()
        self._df = pd.DataFrame()
        self.accepted_mask = pd.Series()
        self._masks_cache = []


    def set_df(self, df):
        self._df = df
        self.accepted_mask = self._alltrues()


    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        return self.accepted_mask.iloc[source_row]


    def custom_filter(self, *args, **kwargs):
        pass


    def string_filter(self, text: str):
        text = text.lower()
        colname = self._colname()
        if text == '':
            mask = self._alltrues()
        else:
            mask = self._df[colname].astype('str').str.lower().str.contains(text)
        self.accepted_mask = mask
        self.invalidate()

    
    def isin_filter(self, values):
        colname = self._colname()
        print('DataFrameSortFilterProxy.isin_filter:'
            ' check if ints will not become float strings...')
        mask = self._df[colname].astype('str').isin(values)
        self.accepted_mask = mask
        self.invalidate()


    def reset_filter(self):
        self.accepted_mask = self._alltrues()
        self.invalidateFilter()


    def _update_accepted(self, mask: pd.Series):
        self._masks_cache.append((self._colnname(), mask))
        self.accepted_mask = self.accepted_mask & mask


    def _colname(self) -> str:
        return self._df.columns[self.filterKeyColumn()]


    def _alltrues(self) -> pd.Series:
        return pd.Series(data=True, index=self._df.index)


class DataFrameView(QTableView):

    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super(DataFrameView, self).__init__(parent)

        self.header_model = CustomHeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self.header_model)

        self.model = DataFrameModel(df=df, header_model=self.header_model, parent=self)
        self.header_model.filter_btn_mapper.mapped[str].connect(self.filter_clicked)

        self.proxy = DataFrameSortFilterProxy()
        self.proxy.set_df(df)
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)

        self.horizontalScrollBar().valueChanged.connect(self.model.on_horizontal_scroll)
        self.horizontalScrollBar().valueChanged.connect(self.model.on_vertical_scroll)

        delegate = DataFrameDelegate(self)
        self.setItemDelegate(delegate)

        # # Create header menu bindings
        # self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        # self.horizontalHeader().customContextMenuRequested.connect(self._header_menu)


    @property
    def df(self):
        return self.model.df

    @df.setter
    def df(self, df: pd.DataFrame):
        # Use the "hard setting" of the dataframe because anyone who's interacting with the
        #  DataFrameWidget (ie, end user) would be setting this
        self.model.df(df)

    def filter_clicked(self, name):
        btn = self.header_model.filter_btn_mapper.mapping(name)

        col_ndx = self.df.columns.get_loc(name)
        self.proxy.setFilterKeyColumn(col_ndx)

        # TODO: look for other ways to position the menu
        header_pos = self.mapToGlobal(btn.parent().pos())
        menu = self.make_header_menu(col_ndx)
        menu_pos = QPoint(header_pos.x() + menu.width() - btn.width() + 5, 
                            header_pos.y() + btn.height() + 15)
        menu.exec_(menu_pos)

        # col_ndx = self.df.columns.get_loc(name)
        # self.proxy.sort(col_ndx, Qt.SortOrder.DescendingOrder)


    def make_cell_context_menu(self, menu, row_ndx, col_ndx):
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
        #                 partial(self._data_model.filterFunction, col_ix=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.ge)))
        # menu.addAction("Filter Less Than",
        #                 partial(self._data_model.filterFunction, col_ix=col_ndx,
        #                         function=partial(_cmp_filter, op=operator.le)))
        menu.addAction(self._icon('DialogResetButton'),
                        "Clear",
                        self.proxy.reset_filter)
        menu.addSeparator()

        # Save to Excel
        menu.addAction("Open in Excel", self._to_excel)

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


    def make_header_menu(self, col_ix: int) -> QMenu:
        """Create popup menu used for header"""

        menu = QMenu(self)

        # Filter Menu Action
        str_filter = LineEditMenuAction(self, menu, 'Filter')
        str_filter.returnPressed.connect(menu.close)
        str_filter.textChanged.connect(self.proxy.string_filter)
        menu.addAction(str_filter)

        list_filter = FilterListMenuWidget(self, menu, col_ix)
        menu.addAction(list_filter)
        menu.addAction(self._icon('DialogResetButton'),
                        "Clear Filter",
                        self.proxy.reset_filter)
        
        # Sort Ascending/Decending Menu Action
        menu.addAction(self._icon('TitleBarShadeButton'),
                        "Sort Ascending",
                       partial(self.proxy.sort, col_ix, Qt.AscendingOrder))
        menu.addAction(self._icon('TitleBarUnshadeButton'),
                        "Sort Descending",
                       partial(self.proxy.sort, col_ix, Qt.DescendingOrder))
                 
        menu.addSeparator()

        # Hide
        menu.addAction("Hide Column...", partial(self.hideColumn, col_ix))

        # Unhide column to left and right
        for i in (-1, 1):
            if self.isColumnHidden(col_ix+i):
                menu.addAction(f'Unhide {self.df.columns[col_ix+i]}',
                                partial(self.showColumn, col_ix+i))

        def _unhide_all(hidden: list):
            for ndx in hidden:
                self.showColumn(ndx)

        # Unhide all hidden columns
        hidden_indices = self._get_hidden_column_indices()
        if hidden_indices:
            menu.addAction(f'Unhide All',
                            partial(_unhide_all, hidden_indices))
        
        menu.addSeparator()

        # Filter Button box
        btn_box = QDialogButtonBox(self)
        btn_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(list_filter.apply_and_close)
        btn_box.rejected.connect(menu.close)
        btn_action = QWidgetAction(self)
        btn_action.setDefaultWidget(btn_box)
        menu.addAction(btn_action)
       
        return menu


    def _to_excel(self):
        from subprocess import Popen
        rows = self.proxy.accepted_mask
        columns = self._get_visible_column_names()
        self.df.loc[rows, columns].to_excel('temp.xls', 'Output')
        Popen('temp.xls', shell=True)
        

    def _get_visible_column_names(self) -> list:
        return [self.df.columns[ndx] for ndx in range(self.df.shape[1]) if not self.isColumnHidden(ndx)]


    def _get_hidden_column_indices(self) -> list:
        return [ndx for ndx in range(self.df.shape[1]) if self.isColumnHidden(ndx)]


    def _icon(self, icon_name) -> QIcon:
        """Convenience function to get standard icons from Qt"""
        if not icon_name.startswith('SP_'):
            icon_name = 'SP_' + icon_name
        icon = getattr(QStyle, icon_name, None)
        if icon is None:
            raise Exception("Unknown icon %s" % icon_name)
        return self.style().standardIcon(icon)        


class MainWindow(QMainWindow):

    def __init__(self, df: pd.DataFrame):
        super().__init__()

        self.table = DataFrameView(df, self)
        self.setCentralWidget(self.table)
        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle("Table View")


def mock_df():
    area = pd.Series({0 : 423967.3, 1: 695662.3, 2: 141297.3, 3: 170312.7, 4: 149995.9})
    pop = pd.Series({0 : 38332521, 1: 26448193, 2: 19651127, 3: 19552860, 4: 12882135})
    states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
    df = pd.DataFrame({'states':states, 'area':area, 'pop':pop}, index=range(len(states)))
    return df


if __name__ == "__main__":

    app = QApplication(sys.argv)

    df = mock_df()
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec_())