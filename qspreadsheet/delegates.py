import os
import sys
from typing import (Any, Callable, Dict, Iterable, List, Mapping,
                    Optional, Sequence, Type, TypeVar, Union)
import logging
from datetime import datetime
from functools import wraps

import numpy as np
import pandas as pd

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import DF
from qspreadsheet.custom_widgets import RichTextLineEdit


DateLike = Union[str, datetime, pd.Timestamp, QDate]
logger = logging.getLogger(__name__)


class ColumnDelegate(QStyledItemDelegate):

    def displayData(self, index: QModelIndex, value: Any) -> str:
        return str(value)

    def alignment(self, index: QModelIndex) -> int:
        return int(Qt.AlignLeft | Qt.AlignVCenter)

    def backgroundBrush(self, index: QModelIndex) -> QBrush:
        return None

    def foregroundBrush(self, index: QModelIndex) -> QBrush:
        return None

    def font(self, index: QModelIndex) -> QFont:
        return None


class GenericDelegate(ColumnDelegate):

    def __init__(self, parent=None):
        super(GenericDelegate, self).__init__(parent)
        self.delegates: Dict[int, ColumnDelegate] = {}

    def addColumnDelegate(self, column_index: int, delegate: ColumnDelegate):
        delegate.setParent(self)
        self.delegates[column_index] = delegate

    def removeColumnDelegate(self, column_index: int):
        delegate = self.delegates.pop(column_index, None)
        if delegate is not None:
            delegate.deleteLater()
            del delegate

    def paint(self, painter, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QStyledItemDelegate.createEditor(self, parent, option,
                                                    index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, index)

    def displayData(self, index: QModelIndex, value: Any) -> str:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.displayData(index, value)
        else:
            return super().displayData(index, value)

    def alignment(self, index: QModelIndex) -> int:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.alignment(index)
        return super().alignment(index)

    def backgroundBrush(self, index: QModelIndex) -> QBrush:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.backgroundBrush(index)
        return super().backgroundBrush(index)

    def foregroundBrush(self, index: QModelIndex) -> QBrush:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.foregroundBrush(index)
        return super().foregroundBrush(index)

    def font(self, index: QModelIndex) -> QFont:
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.font(index)
        return super().font(index)


class IntDelegate(ColumnDelegate):

    def __init__(self, parent=None, 
                 minimum: Optional[int] = None, maximum: Optional[int] = None):
        super(IntDelegate, self).__init__(parent)
        self.minimum = minimum or -sys.maxsize - 1
        self.maximum = maximum or sys.maxsize

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QSpinBox(parent)
        editor.setRange(self.minimum, self.maximum)
        editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return editor

    def setEditorData(self, editor: QSpinBox, index: QModelIndex):
        value = int(index.model().data(index, Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor: QSpinBox, model: QAbstractItemModel, index: QModelIndex):
        editor.interpretText()
        model.setData(index, editor.value())

    def alignment(self, index: QModelIndex) -> int:
        return int(Qt.AlignRight | Qt.AlignVCenter)


class FloatDelegate(ColumnDelegate):

    def __init__(self, parent=None, 
                 minimum: Optional[float] = None, maximum: Optional[float] = None):
        super(FloatDelegate, self).__init__(parent)
        self.minimum = minimum or sys.float_info.min
        self.maximum = maximum or sys.float_info.min

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QDoubleSpinBox(parent)
        editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
        value = float(index.model().data(index, Qt.DisplayRole))
        editor.setValue(value)

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex):
        editor.interpretText()
        model.setData(index, editor.value())

    def alignment(self, index: QModelIndex) -> int:
        return int(Qt.AlignRight | Qt.AlignVCenter)


class BoolDelegate(ColumnDelegate):

    def __init__(self, parent=None):
        super(BoolDelegate, self).__init__(parent)
        self.choices = [True, False]
        self.str_choices = list(map(str, self.choices))

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QComboBox(parent)
        editor.addItems(self.str_choices)
        editor.setEditable(True)
        editor.lineEdit().setReadOnly(True)
        editor.lineEdit().setAlignment(Qt.AlignVCenter)
        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setCurrentIndex(self.str_choices.index(value))

    def setModelData(self, editor: QComboBox, model: QAbstractItemModel, index: QModelIndex):
        value = self.choices[editor.currentIndex()]
        model.setData(index, editor.value())

    def alignment(self, index: QModelIndex) -> int:
        return int(Qt.AlignCenter)


class DateDelegate(ColumnDelegate):

    def __init__(self, parent=None,
                 minimum: Optional[DateLike] = None, maximum: Optional[DateLike] = None,
                 date_format='yyyy-MM-dd', nullable=True):
        super(DateDelegate, self).__init__(parent)
        self.minimum = as_qdate(minimum) if minimum else QDate(1970, 1, 1)
        self.maximum = as_qdate(maximum) if maximum else QDate(9999, 1, 1)
        self.date_format = date_format
        self.nullable = nullable

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        logger.debug('createEditor')
        editor = QDateEdit(parent)
        editor.setDateRange(self.minimum, self.maximum)
        editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        editor.setDisplayFormat(self.date_format)
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor: QDateEdit, index: QModelIndex):
        logger.debug('setEditorData')
        model_value = index.model().data(index, Qt.EditRole)
        if pd.isnull(model_value):
            value = QDate.currentDate()
        else:        
            value = as_qdate(model_value)
        editor.setDate(value)

    def setModelData(self, editor: QDateEdit, model: QAbstractItemModel, index: QModelIndex):
        logger.debug('setModelData')
        model.setData(index, pd.to_datetime(editor.date().toPython()))

    def displayData(self, index: QModelIndex, value: pd.Timestamp) -> Any:
        if pd.isnull(value):
            return 'NaT'
        result = as_qdate(value).toString(self.date_format)
        return result

    def alignment(self, index: QModelIndex) -> int:
        return int(Qt.AlignRight | Qt.AlignVCenter)


class StringDelegate(ColumnDelegate):

    def __init__(self, parent=None):
        super(StringDelegate, self).__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex):
        model_value = index.model().data(index, Qt.EditRole)
        if pd.isnull(model_value):
            model_value = ''
        editor.setText(model_value)

    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.text())


class RichTextDelegate(ColumnDelegate):

    def __init__(self, parent=None):
        super(RichTextDelegate, self).__init__(parent)

    def paint(self, painter, option, index: QModelIndex):
        text = index.model().data(index, Qt.DisplayRole)
        palette = QApplication.palette()
        document = QTextDocument()
        document.setDefaultFont(option.font)
        if option.state & QStyle.State_Selected:
            document.setHtml("<font color={}>{}</font>".format(
                palette.highlightedText().color().name(), text))
        else:
            document.setHtml(text)
        painter.save()
        color = (palette.highlight().color()
                 if option.state & QStyle.State_Selected
                 else QColor(index.model().data(index,
                                                Qt.BackgroundColorRole)))
        painter.fillRect(option.rect, color)
        painter.translate(option.rect.x(), option.rect.y())
        document.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index: QModelIndex):
        text = index.model().data(index)
        document = QTextDocument()
        document.setDefaultFont(option.font)
        document.setHtml(text)
        return QSize(document.idealWidth() + 5,
                     option.fontMetrics.height())

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = RichTextLineEdit(parent)
        return editor

    def setEditorData(self, editor: RichTextLineEdit, index: QModelIndex):
        model_value = index.model().data(index, Qt.EditRole)
        if pd.isnull(model_value):
            model_value = ''
        editor.setHtml(model_value)

    def setModelData(self, editor: RichTextLineEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.toSimpleHtml())


def automap_delegates(df: DF) -> Dict[Any, ColumnDelegate]:
    type2delegate = tuple((
        ('object', StringDelegate),
        ('int', IntDelegate),
        ('float', FloatDelegate),
        ('datetime', DateDelegate),
        ('bool', BoolDelegate),
    ))

    dtypes = df.dtypes.astype(str)

    delegates = {}
    for columnname, dtype in dtypes.items():
        for key, delegate_class in type2delegate:
            if key in dtype:
                delegate = delegate_class()
                delegate.setObjectName(str(columnname))
                break
        else:
            delegate = StringDelegate()

        delegates[columnname] = delegate

    return delegates


def as_qdate(datelike: DateLike, format: Optional[str] = None) -> QDate:
    '''Converts date-like value to QDate
    
        Parameters
        ----------
        dt: {str, datetime, pd.Timestamp, QDate}: value to convert

        format: {str}: default=None. Format must be provided if dt is `str`.

        Returns
        -------
        `QDate`
    '''    
    if isinstance(datelike, str):
        datelike = datetime.strptime(datelike, format)
    return datelike if isinstance(datelike, QDate) else QDate(datelike.year, datelike.month, datelike.day)
