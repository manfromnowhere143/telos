from sympy import Rational
from sympy.printing.pycode import mpmath_code

expr = Rational(10**100 + 1, 10**100)
print("RESULT=" + repr(mpmath_code(expr)))
