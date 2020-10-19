from os import path
import sys

import xlwings as xw

from deco import (accepts, debug_accepts, debug_rangetest, debug_returns,
                  rangetest, returns)


@debug_returns(int)
@debug_accepts(a=int, b=int)
def add_nums_correct(a, b):
    return str(a) + str(b)
 
 
# @returns((int, float))
# @debug_accepts(a=int, b=(int, float))
# def add_nums_correctf(a, b):
#     return a + b


@debug_returns((int, float))
@debug_accepts(a=int, b=(int, float))
def add_nums_incorrect(a, b):
    return str(a) + str(b)


def run():

    wb = xw.books.active
    ws = wb.sheets["Sheet1"]

    ws.range("A1").value = "__debug__"
    ws.range("B1").value = __debug__
    
    ws.range("A2").value = "add_nums_correct(3, 5)"
    ws.range("B2").value = add_nums_correct(3, "5")

    ws.range("A3").value = "add_nums_incorrect(3, 5.0)"
    ws.range("B3").value = add_nums_incorrect(3, "5.0")

    # print(add_nums_correct(3, 5))
    # print(add_nums_correctf(3, 5.0))


if __name__ == "__main__":
    fname = path.splitext(path.basename(__file__))[0] + ".xlsm"
    xw.Book(fname).set_mock_caller()
    run()
