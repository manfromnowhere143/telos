from sympy import Symbol
from sympy.simplify.simplify import posify

x = Symbol("x", integer=True)
xp, _ = posify(x)
print("RESULT=" + repr(xp.is_integer))
