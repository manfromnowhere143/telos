from sympy import Matrix, Poly, symbols

x = symbols("x")
try:
    result = Matrix([[1]]) * Poly(x)
except Exception as exc:
    result = type(exc).__name__

print("RESULT=" + repr(result))
