from sympy import Not, Symbol
from sympy.printing.pycode import PythonCodePrinter

x = Symbol("x", boolean=True)
result = PythonCodePrinter()._print_Not(Not(x))
print("RESULT=" + repr(result))
