from sympy import Symbol
from sympy.polys.domains import EX

f = EX.from_sympy(Symbol("x"))
print("RESULT=" + repr((f != EX.zero, bool(f))))
