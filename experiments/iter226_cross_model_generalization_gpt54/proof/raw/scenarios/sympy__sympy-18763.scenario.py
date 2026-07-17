from sympy import Subs, latex, symbols

x, y = symbols("x y")
result = latex(Subs(x, x, y))
print("RESULT=" + repr(result))
