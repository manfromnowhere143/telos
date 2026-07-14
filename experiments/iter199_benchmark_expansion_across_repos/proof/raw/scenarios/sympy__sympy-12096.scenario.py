from sympy import Rational
from sympy.utilities.lambdify import implemented_function

f = implemented_function("precision_probe_f", lambda x: x)
g = implemented_function("precision_probe_g", lambda x: x)

result = f(g(Rational(1, 3))).evalf(30)
print("RESULT=" + repr(result))
