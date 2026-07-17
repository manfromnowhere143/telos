from sympy import Eq, S, symbols
from sympy.sets.contains import Contains

x = symbols("x")
expr = Contains(Eq(x, x, evaluate=False), S.Reals, evaluate=False)
print("RESULT=" + repr(expr.binary_symbols))
