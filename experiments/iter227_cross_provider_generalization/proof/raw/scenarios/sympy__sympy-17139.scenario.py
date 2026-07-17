from sympy import I, sin, symbols
from sympy.simplify.fu import TR5

x = symbols("x")
result = TR5(sin(x)**I)
print("RESULT=" + repr(result))
