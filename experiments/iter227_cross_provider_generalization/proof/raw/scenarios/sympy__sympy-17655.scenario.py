from sympy import Point, symbols

factor = symbols("factor")
result = Point(1, 2, evaluate=False).__mul__(factor)
print("RESULT=" + repr(result))
