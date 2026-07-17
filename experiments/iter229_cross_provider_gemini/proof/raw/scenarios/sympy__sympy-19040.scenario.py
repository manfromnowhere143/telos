from sympy import Poly, sqrt, symbols
from sympy.polys.domains import QQ
from sympy.polys.factortools import dmp_ext_factor

x, y = symbols("x y")
K = QQ.algebraic_field(sqrt(2))
f = Poly((x + sqrt(2)*y)**2, x, y, domain=K).rep.to_list()

result = dmp_ext_factor(f, 1, K)
print("RESULT=" + repr(result))
