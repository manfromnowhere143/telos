from sympy import Indexed, Symbol
from sympy.printing.pycode import pycode

base = Symbol("lambda")
index = Symbol("i")
print("RESULT=" + repr(pycode(Indexed(base, index))))
