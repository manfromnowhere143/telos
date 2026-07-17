import sympy as sp
from sympy.core.function import Function

class F(Function):
    _imp_ = staticmethod(lambda x: float(x))

result = F(sp.Integer(2))._eval_evalf(53)
print("RESULT=" + repr(result))
