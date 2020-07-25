#In[0]
import sys, os
from fx import fx
from fx.deco import accepts

@accepts(x=(float, int), y=int)
def add(x, y):
    return x + y


print(add(5.5, 5))