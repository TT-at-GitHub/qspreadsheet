import sys, os
import typing
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QHeaderView, QWidget

COL_1, COL_2 = range(2)
VERTICAL_MARGIN = 2


class ColumnHeaderWidget(QWidget):

    def __init__(self, labelText="", parent=None):
        super(ColumnHeaderWidget, self).__init__(parent)
        self.label = QtWidgets.QLabel(labelText)
        self.button = QtWidgets.QPushButton('..')
        self.label.setBuddy(self.button)
        
        # size policy
        sp_left = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sp_left.setHorizontalStretch(4)
        sp_right = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sp_right.setHorizontalStretch(1)
        self.label.setSizePolicy(sp_left)
        self.button.setSizePolicy(sp_right)
        
        self.button.setMinimumWidth(25)
        self.button.setMaximumWidth(30)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        self.setLayout(layout)


class MyHeaderView(QtWidgets.QHeaderView):
    
    def __init__(self, parent=None) -> None:
        super().__init__(QtCore.Qt.Horizontal, parent)
        self.column1 = ColumnHeaderWidget('test1')
        self.column2 = ColumnHeaderWidget('test2')
        
        # compute once and for all the height of our filter row
        self._filter_height = max(
            self.column1.sizeHint().height(),
            self.column2.sizeHint().height())

        self.sectionResized.connect(self.on_sectionResized)

        self.column1.setText('filter text')


    def filter_widget(self, logicalIndex) -> QWidget:
        if logicalIndex == COL_1:
            return self.column1
        elif logicalIndex == COL_2:
            return self.column2
        else:
            return None

    def sizeHint(self) -> QtCore.QSize:
        # insert space for our filter row
        super_sz_h = super().sizeHint()
        
        return QtCore.QSize(super_sz_h.width(), 
            super_sz_h.height() + self._filter_height + 2 * VERTICAL_MARGIN)

    # @QtCore.pyqtSlot()
    def onScroll(self, value):
        vg = self.viewport().geometry()

        # now let's position our widgets
        start = self.visualIndexAt(vg.left())
        end = self.visualIndexAt(vg.right())
        if start == -1:
            start = 0
        if end == -1:
            end = self.count() -1

        self._repositionFilterRow(start, end)

    def updateGeometries(self) -> None:
        vg = self.viewport().geometry()

        # add margins to the QHeaderView so that we reserve the remaining space 
        #to position our filter widgets
        self.setViewportMargins(0, 0, 0, self._filter_height)

        # call parent (which will recompute internal position of sections...)
        super().updateGeometries()
        start = self.visualIndexAt(vg.left())
        end = self.visualIndexAt(vg.right())        
        if start == -1:
            start = 0
        if end == -1:
            end = self.count() -1
            
        self._repositionFilterRow(start, end)        

    
    def on_sectionResized(self, logicalIndex, oldSize, newSize):
        vg = self.viewport().geometry()
        start = self.visualIndex(logicalIndex)
        end = self.visualIndexAt(vg.right())
        if end == -1:
            end = self.count() -1
        self._repositionFilterRow(start, end)

    def _repositionFilterRow(self, start, end):

        for i in range(start, end + 1):
            logical = self.logicalIndex(i)
            if self.isSectionHidden(logical):
                continue

            w = self.filter_widget(logical)
            if w is not None:
                w.move(self.sectionPosition(logical) - self.offset(), self._filter_height)
                w.resize(self.sectionSize(logical), self._filter_height)


class MyModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None) -> None:
        QtCore.QAbstractTableModel.__init__(self, parent=parent)

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return 30

    def columnCount(self, parent: QtCore.QModelIndex) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: int) -> typing.Any:
        if role == QtCore.Qt.DisplayRole:
            return index.row() * self.columnCount(QtCore.QModelIndex()) + index.column()

        return QtCore.QVariant()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int) -> typing.Any:
        # if orientation == QtCore.Qt.Horizontal:
        #     orientation << "(HORIZONTAL)"
        # else:
        #     orientation << "(N/A)"

        # orientation << ",\nrole" << role

        # if role == QtCore.Qt.DisplayRole:
        #     orientation << "(DisplayRole)"
        # else:
        #     orientation << "(N/A)"
        
        # orientation << "\n"
        
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole and section >= 0:
            names = ['test1', 'test2']
            return names[section]

        return QtCore.QVariant()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    view = QtWidgets.QTableView()
    model = MyModel()
    header = MyHeaderView()

    view.setModel(model)
    view.setHorizontalHeader(header)
    view.horizontalScrollBar().valueChanged.connect(header.onScroll)
    vb = view.verticalScrollBar().valueChanged.connect(header.onScroll)
    
    view.show()
    sys.exit(app.exec_())