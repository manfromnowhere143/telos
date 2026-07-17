from sympy import Symbol
from sympy.simplify.simplify import posify

x = Symbol("x", integer=True)
positive_x, _ = posify(x)
print("RESULT=" + repr(positive_x.is_integer))
