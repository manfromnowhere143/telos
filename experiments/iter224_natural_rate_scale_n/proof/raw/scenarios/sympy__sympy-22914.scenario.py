from sympy import Min, symbols
from sympy.printing.pycode import pycode

x, y = symbols("x y")
print("RESULT=" + repr(pycode(Min(x, y))))
