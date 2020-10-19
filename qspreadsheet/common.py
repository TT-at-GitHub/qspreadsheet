import pandas as pd 
from typing import TypeVar
import collections
import six


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