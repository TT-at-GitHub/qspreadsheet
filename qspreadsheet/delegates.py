import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qspreadsheet import DF
from qspreadsheet.custom_widgets import RichTextLineEdit


class GenericDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(GenericDelegate, self).__init__(parent)
        self.delegates = {}

    def insertColumnDelegate(self, column, delegate):
        delegate.setParent(self)
        self.delegates[column] = delegate

    def removeColumnDelegate(self, column):
        if column in self.delegates:
            del self.delegates[column]

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


class IntDelegate(QStyledItemDelegate):

    def __init__(self, minimum=0, maximum=100, parent=None):
        super(IntDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

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


class FloatDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(FloatDelegate, self).__init__(parent)

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


class BoolDelegate(QStyledItemDelegate):

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


class DateDelegate(QStyledItemDelegate):

    def __init__(self, minimum=QDate(),
                 maximum=QDate.currentDate(),
                 format="yyyy-MM-dd", parent=None):
        super(DateDelegate, self).__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.format = format

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QDateEdit(parent)
        editor.setDateRange(self.minimum, self.maximum)
        editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        editor.setDisplayFormat(self.format)
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor: QDateEdit, index: QModelIndex):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setDate(value)

    def setModelData(self, editor: QDateEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.date())


class StringDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(StringDelegate, self).__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(value)

    def setModelData(self, editor: QLineEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.text())


class RichTextDelegate(QStyledItemDelegate):

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
        value = index.model().data(index, Qt.DisplayRole)
        editor.setHtml(value)

    def setModelData(self, editor: RichTextLineEdit, model: QAbstractItemModel, index: QModelIndex):
        model.setData(index, editor.toSimpleHtml())


def automap_delegates(df: DF) -> Dict[Any, QStyledItemDelegate]:
    type2delegate = tuple((
        ('object', StringDelegate),
        ('int', IntDelegate)
    ))
    return {}