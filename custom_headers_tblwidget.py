import sys, os
from PyQt5.QtWidgets import (QApplication, QDialog
    , QWidget, QHeaderView, QTableWidget, QComboBox
    , QTableWidgetItem, QLabel, QPushButton, QHBoxLayout
    , QVBoxLayout
    , QGridLayout, QBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QModelIndex, QSize, QRect, QMargins
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


class CustomTableHeader(QHeaderView):

    class HeaderItem():
        def __init__(self):
            self.w = QWidget()
            self.margins = QMargins()


    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.headers = []
        self.sectionResized.connect(self.on_section_resized)
        self.sectionMoved.connect(self.on_section_moved)

    def showEvent(self, e: QShowEvent):
        for i in range(self.count()):
            if len(self.headers) -1 < i:
                header = CustomTableHeader.HeaderItem()
                self.headers.append(header)
            else:
                header = self.headers[i]

            header.w.setParent(self)
            header.w.setGeometry(
                self.sectionViewportPosition(i) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)
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
                self.sectionViewportPosition(logical) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)

    def on_section_moved(self, logical, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            header = self.headers[i]

            self.headers[logical].w.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)

    def fix_combo_positions(self):
        for i in range(self.count()):
            header = self.headers[i]
            rect = QRect(self.sectionViewportPosition(i) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
                self.height() - header.margins.top() - header.margins.bottom() - 1)
            header.w.setGeometry(rect)

    def set_item_widget(self, index: int, widget: QWidget):
        widget.setParent(self)
        self.headers[index].w = widget
        self.headers[index].margins = QMargins()
        widget.show()
        self.fix_combo_positions()

    def set_item_margin(self, index: int, margins: QMargins):
        self.headers[index].margins = margins


class CustomHeaderedTable(QTableWidget):

    def __init__(self, rows, columns, parent=None):
        super().__init__(rows, columns, parent)
        self._header = CustomTableHeader(self)
        self.setHorizontalHeader(self._header)
        self.setHorizontalHeaderLabels([None for i in range(self._header.count())])

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)

        if dx != 0:
            self._header.fix_combo_positions()

    def setHorizontalHeaderItem(self, column, item):
        self._header.set_item_widget(column, item)

    def set_horizontal_margin(self, column: int, margins: QMargins):
        self._header.set_item_margin(column, margins)


class MainForm(QDialog):

    def __init__(self, tbl: QTableWidget, parent=None):
        super(MainForm, self).__init__(parent)

        listLabel = QLabel("&List")
        self.listWidget = QListWidget()
        listLabel.setBuddy(self.listWidget)

        tableLabel = QLabel("&Table")
        self.tableWidget = QTableWidget()
        tableLabel.setBuddy(self.tableWidget)

        addShipButton = QPushButton("&Add Ship")
        removeShipButton = QPushButton("&Remove Ship")
        quitButton = QPushButton("&Quit")
        if not MAC:
            addShipButton.setFocusPolicy(Qt.NoFocus)
            removeShipButton.setFocusPolicy(Qt.NoFocus)
            quitButton.setFocusPolicy(Qt.NoFocus)

        splitter = QSplitter(Qt.Horizontal)
        vbox = QVBoxLayout()
        vbox.addWidget(listLabel)
        vbox.addWidget(self.listWidget)
        widget = QWidget()
        widget.setLayout(vbox)
        splitter.addWidget(widget)
        vbox = QVBoxLayout()
        vbox.addWidget(tableLabel)
        vbox.addWidget(self.tableWidget)
        widget = QWidget()
        widget.setLayout(vbox)
        splitter.addWidget(widget)
        vbox = QVBoxLayout()
        vbox.addWidget(treeLabel)
        vbox.addWidget(self.treeWidget)
        widget = QWidget()
        widget.setLayout(vbox)
        splitter.addWidget(widget)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(addShipButton)
        buttonLayout.addWidget(removeShipButton)
        buttonLayout.addStretch()
        buttonLayout.addWidget(quitButton)
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        self.tableWidget.itemChanged.connect(self.tableItemChanged)
        addShipButton.clicked.connect(self.addShip)
        removeShipButton.clicked.connect(self.removeShip)
        quitButton.clicked.connect(self.accept)

        self.ships = ships.ShipContainer("ships.dat")
        self.setWindowTitle("Ships (dict)")
        self.setMinimumWidth(960)
        QTimer.singleShot(0, self.initialLoad)


    def initialLoad(self):
        if not QFile.exists(self.ships.filename):
            for ship in ships.generateFakeShips():
                self.ships.addShip(ship)
            self.ships.dirty = False
        else:
            try:
                self.ships.load()
            except IOError as e:
                QMessageBox.warning(self, "Ships - Error",
                        "Failed to load: {}".format(e))
        self.populateList()
        self.populateTable()
        self.tableWidget.sortItems(0)
        self.populateTree()


    def reject(self):
        self.accept()


    def accept(self):
        if (self.ships.dirty and
            QMessageBox.question(self, "Ships - Save?",
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No) ==
                    QMessageBox.Yes):
            try:
                self.ships.save()
            except IOError as e:
                QMessageBox.warning(self, "Ships - Error",
                        "Failed to save: {}".format(e))
        QDialog.accept(self)


    def populateList(self, selectedShip=None):
        selected = None
        self.listWidget.clear()
        for ship in self.ships.inOrder():
            item = QListWidgetItem("{} of {}/{} ({:,})".format(
                     ship.name, ship.owner, ship.country, ship.teu))
            self.listWidget.addItem(item)
            if selectedShip is not None and selectedShip == id(ship):
                selected = item
        if selected is not None:
            selected.setSelected(True)
            self.listWidget.setCurrentItem(selected)


    def populateTable(self, selectedShip=None):
        selected = None
        self.tableWidget.clear()
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setRowCount(len(self.ships))
        headers = ["Name", "Owner", "Country", "Description", "TEU"]
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setHorizontalHeaderLabels(headers)
        for row, ship in enumerate(self.ships):
            item = QTableWidgetItem(ship.name)
            item.setData(Qt.UserRole, int(id(ship)))
            if selectedShip is not None and selectedShip == id(ship):
                selected = item
            self.tableWidget.setItem(row, ships.NAME, item)
            self.tableWidget.setItem(row, ships.OWNER,
                    QTableWidgetItem(ship.owner))
            self.tableWidget.setItem(row, ships.COUNTRY,
                    QTableWidgetItem(ship.country))
            self.tableWidget.setItem(row, ships.DESCRIPTION,
                    QTableWidgetItem(ship.description))
            item = QTableWidgetItem("{:10}".format(ship.teu))
            item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.tableWidget.setItem(row, ships.TEU, item)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.resizeColumnsToContents()
        if selected is not None:
            selected.setSelected(True)
            self.tableWidget.setCurrentItem(selected)


    def populateTree(self, selectedShip=None):
        selected = None
        self.treeWidget.clear()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Country/Owner/Name", "TEU"])
        self.treeWidget.setItemsExpandable(True)
        parentFromCountry = {}
        parentFromCountryOwner = {}
        for ship in self.ships.inCountryOwnerOrder():
            ancestor = parentFromCountry.get(ship.country)
            if ancestor is None:
                ancestor = QTreeWidgetItem(self.treeWidget, [ship.country])
                parentFromCountry[ship.country] = ancestor
            countryowner = ship.country + "/" + ship.owner
            parent = parentFromCountryOwner.get(countryowner)
            if parent is None:
                parent = QTreeWidgetItem(ancestor, [ship.owner])
                parentFromCountryOwner[countryowner] = parent
            item = QTreeWidgetItem(parent, [ship.name, "{:,}".format(ship.teu)])
            item.setTextAlignment(1, Qt.AlignRight|Qt.AlignVCenter)
            if selectedShip is not None and selectedShip == id(ship):
                selected = item
            self.treeWidget.expandItem(parent)
            self.treeWidget.expandItem(ancestor)
        self.treeWidget.resizeColumnToContents(0)
        self.treeWidget.resizeColumnToContents(1)
        if selected is not None:
            selected.setSelected(True)
            self.treeWidget.setCurrentItem(selected)


    def addShip(self):
        ship = ships.Ship(" Unknown", " Unknown", " Unknown")
        self.ships.addShip(ship)
        self.populateList()
        self.populateTree()
        self.populateTable(id(ship))
        self.tableWidget.setFocus()
        self.tableWidget.editItem(self.tableWidget.currentItem())


    def tableItemChanged(self, item):
        ship = self.currentTableShip()
        if ship is None:
            return
        column = self.tableWidget.currentColumn()
        if column == ships.NAME:
            ship.name = item.text().strip()
        elif column == ships.OWNER:
            ship.owner = item.text().strip()
        elif column == ships.COUNTRY:
            ship.country = item.text().strip()
        elif column == ships.DESCRIPTION:
            ship.description = item.text().strip()
        elif column == ships.TEU:
            ship.teu = int(item.text())
        self.ships.dirty = True
        self.populateList()
        self.populateTree()


    def currentTableShip(self):
        item = self.tableWidget.item(self.tableWidget.currentRow(), 0)
        if item is None:
            return None
        return self.ships.ship(int(item.data(Qt.UserRole)))


    def removeShip(self):
        ship = self.currentTableShip()
        if ship is None:
            return
        if (QMessageBox.question(self, "Ships - Remove", 
                "Remove {} of {}/{}?".format(ship.name, ship.owner, ship.country),
                QMessageBox.Yes|QMessageBox.No) ==
                QMessageBox.No):
            return
        self.ships.removeShip(ship)
        self.populateList()
        self.populateTree()
        self.populateTable()


if __name__ == "__main__":

    app  = QApplication(sys.argv)
    tbl = CustomHeaderedTable(10, 3)
    tbl.show()

    col = ColumnHeaderWidget('header1')
    tbl.setHorizontalHeaderItem(0, col)
    tbl.resize(800, 600)

    form = MainForm()
    form.show()
    app.exec_()
    sys.exit(app.exec_())
