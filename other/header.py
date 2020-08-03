import sys, os
import typing
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
            font: bold 14px 'Consolas'; ''')

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
            self._set_item_geometry(self.headers[logical], logical)


    def _set_item_geometry(self, item: HeaderItem, logical:int):
        item.widget.setGeometry(
            self.sectionViewportPosition(logical), 0,
            self.sectionSize(logical) - item.margins.left() - item.margins.right() - 1,
            self.height() + item.margins.top() + item.margins.bottom() - 1)


    def on_section_moved(self, logical, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            header = self.headers[i]

            self.headers[logical].widget.setGeometry(
                self.sectionViewportPosition(logical) + header.margins.left(),
                header.margins.top(),
                self.sectionSize(i) - header.margins.left() - header.margins.right() -1,
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
