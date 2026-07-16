from sympy import I, Symbol, cos, simplify

x = Symbol("x")
try:
    result = simplify(cos(x)**I)
except Exception as exc:
    result = ("EXCEPTION", type(exc).__name__)

print(f"RESULT={result!r}")
