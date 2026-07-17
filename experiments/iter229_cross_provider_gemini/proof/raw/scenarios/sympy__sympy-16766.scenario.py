from sympy import And, Not, symbols
from sympy.printing.pycode import PythonCodePrinter

x, y = symbols("x y")
expr = Not(And(x, y, evaluate=False), evaluate=False)
print("RESULT=" + repr(PythonCodePrinter()._print_Not(expr)))
