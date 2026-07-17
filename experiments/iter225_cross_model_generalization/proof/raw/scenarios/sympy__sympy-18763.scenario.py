from sympy import Subs, latex, symbols

x = symbols("x")
print("RESULT=" + repr(latex(Subs(x, x, 1))))
