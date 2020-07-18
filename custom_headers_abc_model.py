import sys, os
import typing
from PyQt5.QtWidgets import (QApplication, QDialog
    , QWidget, QHeaderView, QTableWidget, QComboBox
    , QTableWidgetItem, QLabel, QPushButton, QHBoxLayout
    , QVBoxLayout, QGridLayout, QBoxLayout, QSizePolicy
    , QTableView)
from PyQt5.QtCore import (Qt, QModelIndex, QSize, QRect
    , QMargins, QAbstractTableModel, QVariant)
from PyQt5.QtGui import (QShowEvent, QColor, QPixmap
    , QIcon, QFont, QTransform, QPalette)


class ColumnHeaderWidget(QWidget):

    def __init__(self, labelText="", parent=None):
        super(ColumnHeaderWidget, self).__init__(parent)
        self.label = QLabel(labelText)
        self.button = QPushButton('')
        self.button.setIconSize(QSize(12, 12))
        self.label.setBuddy(self.button)

        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.label.setFont(font)
        self.button.setFont(font)
        self.button.setFixedSize(QSize(25, 20))
        icon = QIcon((QPixmap("./images/next.svg")
                    .transformed(QTransform().rotate(90))))
        self.button.setIcon(icon)

        layout = QHBoxLayout()
        layout.addWidget(self.label, 4, Qt.AlignJustify)
        layout.addWidget(self.button, 1, Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumHeight(20)


class CustomHeaderView(QHeaderView):

    class HeaderItem():
        def __init__(self):
            self.w = QWidget()
            self.margins = QMargins(2, 2, 2, 2)


    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.headers = []
        self.sectionResized.connect(self.on_section_resized)
        self.sectionMoved.connect(self.on_section_moved)

    def showEvent(self, e: QShowEvent):
        for i, header in enumerate(self.headers):
            header.w.setParent(self)
            self._set_item_geometry(self.headers[i], i)
            header.w.show()

        super().showEvent(e)

    def sizeHint(self) -> QSize:
        # insert space for our filter row
        super_sz_h = super().sizeHint()

        return QSize(super_sz_h.width(),
            super_sz_h.height() + 5)

    def on_section_resized(self, i):
        headers = self.headers[i:]
        for ndx, header in enumerate(headers):
            logical = self.logicalIndex(ndx)
            self._set_item_geometry(self.headers[logical], logical)

    def _set_item_geometry(self, item: HeaderItem, ndx: int):
        item.w.setGeometry(
            self.sectionViewportPosition(ndx), 0,
            self.sectionSize(ndx) - 5, self.height())


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


class MyTableModel(QAbstractTableModel):

    def __init__(self, parent=None) -> None:
        QAbstractTableModel.__init__(self, parent=parent)
        self.header_model = CustomHeaderView()

    def rowCount(self, parent: QModelIndex) -> int:
        return 15

    def columnCount(self, parent: QModelIndex) -> int:
        return 2

    def data(self, index: QModelIndex, role: int) -> typing.Any:
        if role == Qt.DisplayRole:
            return index.row() * self.columnCount(QModelIndex()) + index.column()

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Any:

        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section >= 0:
            if len(self.header_model.headers) -1 < section:
                header = CustomHeaderView.HeaderItem()
                header.w = QComboBox()
                header.w.addItem('Column {}'.format(section + 1))
                self.header_model.headers.append(header)
            return self.header_model.headers[section]

        return QVariant()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    table = QTableView()
    model = MyTableModel()
    table.setModel(model)
    table.setHorizontalHeader(model.header_model)
    table.setMinimumSize(600, 450)
    table.show()
    sys.exit(app.exec_())