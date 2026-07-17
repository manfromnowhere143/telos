from sympy import Float
from sympy.printing.pycode import MpmathPrinter

printer = MpmathPrinter({"full_prec": "auto"})
result = printer._print_Float(Float("1.234567890123456789", precision=80))
print("RESULT=" + repr(result))
