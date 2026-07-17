from sympy import Symbol
from sympy.simplify.simplify import posify

x = Symbol("x", integer=True)
y, _ = posify(x)
print("RESULT=" + repr((y.is_integer, y.is_rational)))
