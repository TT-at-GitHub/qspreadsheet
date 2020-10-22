import pandas as pd 
from typing import TypeVar
import collections
import six
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QStyle


MAX_INT = 2147483647
MAX_FLOAT = 3.4028234664e+38
LEFT, ABOVE = range(2)

DF = TypeVar('DF', bound=pd.DataFrame)
SER = TypeVar('SER', bound=pd.Series)


def is_iterable(arg):
    return (
        isinstance(arg, collections.Iterable) 
        and not isinstance(arg, six.string_types)
    )

def standard_icon(icon_name: str) -> QIcon:
    '''Convenience function to get standard icons from Qt'''
    if not icon_name.startswith('SP_'):
        icon_name = 'SP_' + icon_name
    icon = getattr(QStyle, icon_name, None)
    if icon is None:
        raise Exception("Unknown icon {}".format(icon_name))
    return QApplication.style().standardIcon(icon)
