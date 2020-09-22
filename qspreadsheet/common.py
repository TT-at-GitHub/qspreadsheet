import pandas as pd 
from typing import TypeVar


MAX_INT = 2147483647
LEFT, ABOVE = range(2)

DF = TypeVar('DF', bound=pd.DataFrame)
SER = TypeVar('SER', bound=pd.Series)
