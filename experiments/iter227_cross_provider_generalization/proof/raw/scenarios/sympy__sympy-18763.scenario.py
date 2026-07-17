from sympy import Subs, Symbol, latex

x = Symbol("x")
y = Symbol("y")
print("RESULT=" + repr(latex(Subs(x, x, y))))
