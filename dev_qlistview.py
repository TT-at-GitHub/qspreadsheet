import os, sys
from typing import cast
import numpy as np 
import pandas as pd 
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import PySide2
plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

app = QApplication(sys.argv)

df = pd.DataFrame(pd.read_pickle('.ignore/data/10rows.pkl'))
column = df.B

class MyProxy(QSortFilterProxyModel):
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row == 0:
            return True
        return super().filterAcceptsRow(source_row, source_parent)

class MainWindow(QMainWindow):

    def __init__(self, parent=None) -> None:
        super(MainWindow, self).__init__(parent)

        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)
        
        
        self.model = QStandardItemModel(df.index.size, 1)
        self.proxy = MyProxy(central_widget)
        self.proxy.setSourceModel(self.model)

        for i, value in enumerate(column, start=1):
            item = QStandardItem(value)
            item.setCheckable(True)
            item.setData(Qt.Checked, Qt.CheckStateRole)
            self.model.setItem(i, item)

        item = QStandardItem('(Select All)')
        item.setCheckable(True)
        item.setData(Qt.Checked, Qt.CheckStateRole)
        self.model.setItem(0, item)

        self.view = QListView(central_widget)
        self.view.setModel(self.proxy)
        self.model.itemChanged.connect(self.on_item_changed)

        line_edit = QLineEdit(central_widget)
        line_edit.textChanged.connect(self.on_text_changed)
        
        central_layout.addWidget(self.view)
        central_layout.addWidget(line_edit)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)


    def on_text_changed(self, text):
        print(text)
        self.proxy.setFilterRegExp(QRegExp(text,
            Qt.CaseInsensitive, QRegExp.FixedString))
        self.proxy.setFilterKeyColumn(0)
        
        print('proxy.rowCount: ', self.proxy.rowCount(QModelIndex()))
        print('model.rowCount: ', self.model.rowCount(QModelIndex()))


    def on_item_changed(self, item):
        print(type(item))
        it = cast(QStandardItem, item)
        if it:
            print(it.text())
        print('\n-----')

w = MainWindow()
w.show()
sys.exit(app.exec_())