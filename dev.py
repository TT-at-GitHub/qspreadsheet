#In[0]
import sys, os
import numpy as np
import pandas as pd 
import PySide2

plugin_path = os.path.join(os.path.dirname(PySide2.__file__), 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

#In[0]
rng = np.random.RandomState(42)
data = pd.DataFrame(rng.randint(0, 10, (3, 4)), columns=['A', 'B', 'C', 'D'])
data

# %%
