import sys, os
from PyQt5.QtWidgets import (QApplication, QDialog
    , QWidget, QHeaderView, QTableWidget, QComboBox
    , QTableWidgetItem, QLabel, QPushButton, QHBoxLayout
    , QVBoxLayout
    , QGridLayout, QBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QModelIndex, QSize
from PyQt5.QtGui import QShowEvent, QColor


class ColumnHeaderWidget(QWidget):

    def __init__(self, labelText="", parent=None):
        super(ColumnHeaderWidget, self).__init__(parent)
        self.label = QLabel(labelText)
    # header.setBackground(QColor(85, 85, 125))

        self.button = QPushButton('..')
        self.label.setBuddy(self.button)
        
        # # size policy
        # sp_left = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # sp_left.setHorizontalStretch(4)
        # sp_right = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        # sp_right.setHorizontalStretch(1)
        # self.label.setSizePolicy(sp_left)
        # self.button.setSizePolicy(sp_right)
        
        self.label.setFixedHeight(20)
        self.button.setFixedSize(QSize(25, 20))

        layout = QHBoxLayout()
        layout.addWidget(self.label, 4, Qt.AlignJustify)
        layout.addWidget(self.button, 1, Qt.AlignRight)

        self.setLayout(layout)
        self.setMinimumHeight(25)

# app  = QApplication(sys.argv)
# dlg = QDialog()
# lay = QVBoxLayout()
# col = ColumnHeaderWidget('header1')
# lay.addWidget(col)
# dlg.setLayout(lay)

# dlg.show()
# sys.exit(app.exec_())

class Margins():

    def __init__(self, l=0, r=0, t=0, b=0):
        self.left = l
        self.right = r
        self.top = t
        self.bottom = b


class CustomTableHeader(QHeaderView):
    class HeaderItem():
        def __init__(self):
            self.w = None
            self.margins = None

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.headers = []
        self.sectionResized.connect(self.on_section_resized)
        self.sectionMoved.connect(self.on_section_moved)

    def showEvent(self, e: QShowEvent):
        for i in range(self.count()):
            if len(self.headers) -1 < i:
                header = CustomTableHeader.HeaderItem()
                header.w = QWidget()
                header.margins = Margins()
                self.headers.append(header)
            else:
                header = self.headers[i]

            header.w.setParent(self)
            header.w.setGeometry(
                self.sectionViewportPosition(i) + header.margins.left,
                header.margins.top,
                self.sectionSize(i) - header.margins.left - header.margins.right -1,
                self.height() - header.margins.top - header.margins.bottom - 1)
            header.w.show()

        return super().showEvent(e)

    def sizeHint(self) -> QSize:
        # insert space for our filter row
        super_sz_h = super().sizeHint()
        
        return QSize(super_sz_h.width(), 
            super_sz_h.height() + 5)

    def on_section_resized(self, i):
        logical = 0
        header = self.headers[i]

        for j in range(self.logicalIndex(i), self.count()):
            logical = self.logicalIndex(j)
            self.headers[logical].w.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left,
                header.margins.top,
                self.sectionSize(i) - header.margins.left - header.margins.right -1,
                self.height() - header.margins.top - header.margins.bottom - 1)

    def on_section_moved(self, logical, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            header = self.headers[i]

            self.headers[logical].w.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left,
                header.margins.top,
                self.sectionSize(i) - header.margins.left - header.margins.right -1,
                self.height() - header.margins.top - header.margins.bottom - 1)

    def fix_combo_positions(self):
        for i in range(self.count()):
            header = self.headers[i]
            header.w.setGeometry(
                self.sectionViewportPosition(i) + header.margins.left,
                header.margins.top,
                self.sectionSize(i) - header.margins.left - header.margins.right -1,
                self.height() - header.margins.top - header.margins.bottom - 1)

    def set_item_widget(self, index: int, widget: QWidget):
        widget.setParent(self)
        self.headers[index].w = widget
        self.headers[index].margins = Margins()
        widget.show()
        self.fix_combo_positions()

    def set_item_margin(self, index: int, margins: Margins):
        self.headers[index].margins = margins


class CustomHeaderedTable(QTableWidget):

    def __init__(self, rows, columns, parent=None):
        super().__init__(rows, columns, parent)
        self._headers = CustomTableHeader(self)
        self.setHorizontalHeader(self._headers)
        self.setHorizontalHeaderLabels([None for i in range(self._headers.count())])
        
        
    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)

        if dx != 0:
            self._headers.fix_combo_positions()

    def setHorizontalHeaderItem(self, column, item):
        self._headers.set_item_widget(column, item)

    def set_horizontal_margin(self, column: int, margins: Margins):    
        self._headers.set_item_margin(column, margins)
if __name__ == "__main__":

    app  = QApplication(sys.argv)
    tbl = CustomHeaderedTable(10, 3)    
    tbl.show()

    col = ColumnHeaderWidget('header1')
    tbl.setHorizontalHeaderItem(0, col)

    tbl.show()
    tbl.resize(800, 600)
    sys.exit(app.exec_())
