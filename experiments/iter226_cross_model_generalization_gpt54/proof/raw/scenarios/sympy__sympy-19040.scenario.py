from sympy import factor_list, sqrt, symbols

x, y = symbols("x y")
result = factor_list((x - sqrt(2)*y)**2, x, y, extension=sqrt(2))
print("RESULT=" + repr(result))
