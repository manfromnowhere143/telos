from sympy import Symbol, latex

x = Symbol("x")
print("RESULT=" + repr(latex(2 * x, mul_symbol=r"\,")))
