from sympy import Rational
from sympy.printing.pycode import mpmath_code

result = mpmath_code(Rational(2, 3))
print("RESULT=" + repr(result))
