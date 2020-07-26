import sys, os
import typing

import numpy as np
import pandas as pd

import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *



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

    class Signals(QObject):
        filter_clicked = Signal(str)

    def __init__(self, columns: list, parent=None):
        super().__init__(Qt.Horizontal, parent)

        self.headers = []
        # self.signals = CustomHeaderView.Signals()
        self.filter_btn_mapper = QSignalMapper(self)

        for i, name in enumerate(columns):
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

    def filter_clicked(self, s: str):
        btn = self.filter_btn_mapper.mapping(s)
        print('Change the icon here!')

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

        self.logical = None
        self.dirty = False

        self._header_model = header_model
        self._header_model.filter_btn_mapper.mapped[str].connect(self.filter_clicked)
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


class DataFrameView(QTableView):

    df_changed = Signal()
    cell_clicked = Signal(int, int)

    def __init__(self, parent=None, df=None) -> None:
        super(DataFrameView, self).__init__(parent)

        # Set the views
        self._header_model = HeaderView(columns=df.columns.tolist())
        self.setHorizontalHeader(self._header_model)

        self._data_model = DataFrameModel(data=df, header_model=self._header_model, parent=self)
        self.setModel(self._data_model)

        # Signals/Slots
        self._data_model.modelReset.connect(self.df_changed)
        self._data_model.dataChanged.connect(self.df_changed)
        self.clicked.connect(self.on_click)

        self.horizontalScrollBar().valueChanged.connect(self._data_model.on_horizontal_scroll)
        self.horizontalScrollBar().valueChanged.connect(self._data_model.on_vertical_scroll)

        item_delegete = DataFrameItemDelegate()
        self.setItemDelegate(item_delegete)


    def set_df(self, df: pd.DataFrame):
        self._data_model


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
        self.table = DataFrameView(self)
        self.table.set_df(df)
        self.setCentralWidget(self.table)

        # Set window size
        col_width = sum([self.table.columnWidth(i) for i in range(df.shape[1])])
        col_width = min(col_width + MainWindow.MARGIN * 2, 1280)
        self.setGeometry(200, 300, col_width, 300)
        self.setMinimumSize(QSize(400, 300))


    def filter_clicked(self, name):
        print(self.__class__.__name__, ': ', name)
        ndx = self._df.columns.get_loc(name)
        self.logical = self.logicalIndex(ndx)

        self.filter_menu = QMenu(self)
        self.filter_values_mapper
        unique_values = self._df[name].unique()

        action_all = QAction('All', self)
        action_all.triggered.connect(self.on_action_all_triggered)
        self.filter_menu.addAction(action_all)
        self.filter_menu.addSeparator()

        for i, name in enumerate(sorted(unique_values)):
            action = QAction(name, self)
            self.filter_values_mapper.setMapping(action, i)
            action.triggered.connect(self.filter_values_mapper.map)
            self.filter_menu.addAction(action)


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