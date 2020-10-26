import sys, os
from typing import cast

import numpy as np
import pandas as pd

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

from fx import fx
from qspreadsheet import DataFrameView, automap_delegates, IntDelegate
from qspreadsheet import resources_rc

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)-8s [%(name)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self, table_view: DataFrameView):
        super(MainWindow, self).__init__()

        self.table = table_view
        self.table.model().dataChanged.connect(self.on_data_changed)

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        central_widget.setLayout(layout)

        table_hlayout = QHBoxLayout()
        central_widget.setLayout(table_hlayout)
        table_hlayout.addWidget(table_view)
        layout.addLayout(table_hlayout)

        buttons_hlayout = QHBoxLayout()
        buttons_hlayout.addStretch()

        for name, slot in (('Save', self.on_save),
                           ('Close', self.on_close)):
            btn = QPushButton(name)
            btn.setObjectName(name)
            btn.clicked.connect(slot)
            buttons_hlayout.addWidget(btn)
        layout.addLayout(buttons_hlayout)

        self.save_button = cast(QPushButton, central_widget.findChild(QPushButton, 'Save'))
        self.save_button.setEnabled(False)

        self.setCentralWidget(central_widget)
        self.load_window_settings()
        self.setWindowTitle("Table View")

    def closeEvent(self, event: QCloseEvent):
        self.save_window_settings()
        event.accept()

    def save_window_settings(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                             'TT', 'qspreadsheet')
        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
        settings.endGroup()

    def load_window_settings(self):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                             'TT', 'qspreadsheet')
        settings.beginGroup('MainWindow')
        self.resize(QSize(settings.value('size', QSize(960, 640))))
        self.move(QPoint(settings.value('pos', QPoint(200, 200))))
        settings.endGroup()

    def on_save(self):
        logging.debug('on_save')
        self.save_button.setEnabled(False)

    def on_close(self):
        logging.debug('on_close')
        self.close()

    def on_data_changed(self, first: QModelIndex, last: QModelIndex):
        if self.table.is_dirty:
            self.save_button.setEnabled(True)
            logger.debug('Save button enabled: True')
        else:
            logger.debug('Save button enabled: False')
            self.save_button.setEnabled(False)


app = QApplication(sys.argv)

# df = mock_df()
df = pd.DataFrame(pd.read_pickle('.ignore/data/10rows.pkl'))
df = df.sort_values(by='C').reset_index(drop=True)
# print(df)

pd.options.display.precision = 4

delegates = automap_delegates(df, nullable=True)
# delegates['div'] = IntDelegate().to_nullable()
# bools = delegates['bools'].to_non_nullable()
# delegates['bools'] = bools

table_view = DataFrameView(df=df, delegates=delegates)
table_view.set_columns_edit_state(df.columns.tolist(), True)
# table_view.set_columns_edit_state('div', False)
table_view.set_columns_edit_state('C', False)


window = MainWindow(table_view=table_view)

window.show()
sys.exit(app.exec_())
