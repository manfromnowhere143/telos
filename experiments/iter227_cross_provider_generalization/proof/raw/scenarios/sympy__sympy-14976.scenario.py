import sympy
from sympy.printing.pycode import MpmathPrinter

result = MpmathPrinter()._print_Float(sympy.Float("1.25"))
print("RESULT=" + repr(result))
