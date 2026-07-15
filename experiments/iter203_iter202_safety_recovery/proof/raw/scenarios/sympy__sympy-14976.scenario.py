from sympy import Rational
from sympy.printing.pycode import MpmathPrinter

result = MpmathPrinter().doprint(Rational(232, 3))
print("RESULT=" + repr(result))
