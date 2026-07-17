from sympy import Subs, latex, symbols

x = symbols("x")
result = latex(Subs(x + 1, x, 2))
print("RESULT=" + repr(result))
