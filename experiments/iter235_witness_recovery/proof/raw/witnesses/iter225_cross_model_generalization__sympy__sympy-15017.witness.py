try:
    import sympy

    if not hasattr(sympy, "Array"):
        raise AttributeError("Array")

    array = sympy.Array(3)
    result = (len(array), len(list(array)))
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
