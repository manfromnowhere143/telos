from sympy import I, sin, symbols
from sympy.simplify.fu import TR5

x = symbols("x")
try:
    result = TR5(sin(x)**I)
except Exception as exc:
    result = ("EXCEPTION", type(exc).__name__)

print("RESULT=" + repr(result))
