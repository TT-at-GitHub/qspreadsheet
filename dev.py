#In[0]
import sys, os
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import numpy as np
import pandas as pd 
from datetime import datetime, timedelta
from fx import fx
import qspreadsheet as qss

import PySide2
plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

dt = datetime(2000, 7, 5)
data = [
    [5, 'Jim Carray',       dt + timedelta(days=1), True, 7.3],
    [11, 'Kate Beckinsale', dt + timedelta(days=2), False, 1.69],
    [9, 'Jim Carray',       dt + timedelta(days=4), True, 3.33],
    [3, 'Jim Carray',       dt + timedelta(days=6), True, 14.12]
    ]


df = pd.DataFrame(data = data, columns=list('NSDBF'))
df



#In[0]
dftypes = df.dtypes.map(str)
dftypes
#In[0]

# print(df.columns[dftypes.str.contains('float')])
# print(df.columns[dftypes.str.contains('int')])
# print(df.columns[dftypes.str.contains('bool')])
print(df.columns[dftypes.str.contains('date')])
# print(df.columns[dftypes.str.contains('object')])
df[df.columns[dftypes.str.contains('date')]]
#In[0]

df.select_dtypes(include=['float32', 'float64'])
df.dtypes
#In[0]

app = QApplication(sys.argv)

df = mock_df()
window = MainWindow(df)
window.show()
sys.exit(app.exec_())
