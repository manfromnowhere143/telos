from sympy import Subs, latex, symbols

x, y = symbols("x y")
expr = Subs(x*y, (x,), (1,))
print("RESULT=" + repr(latex(expr)))
