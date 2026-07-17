from sympy import I, symbols

x, y = symbols("x y", real=True)
expr = I*x + I*y
print("RESULT=" + repr(expr._eval_is_zero()))
