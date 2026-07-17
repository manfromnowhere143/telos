from sympy import Add, symbols

x, y = symbols("x y", zero=True)
expr = Add(x, y)
print("RESULT=" + repr(expr._eval_is_zero()))
