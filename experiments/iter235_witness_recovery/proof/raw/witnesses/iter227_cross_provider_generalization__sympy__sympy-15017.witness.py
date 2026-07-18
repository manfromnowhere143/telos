import sympy

try:
    class FalseShape(tuple):
        def __bool__(self):
            return False

    array = sympy.Array([7, 8], FalseShape((2,)))
    result = len(array)
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
