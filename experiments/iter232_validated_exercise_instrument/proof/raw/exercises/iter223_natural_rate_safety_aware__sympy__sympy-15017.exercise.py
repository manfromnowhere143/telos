try:
    import sympy

    arrays = [sympy.Array(3), sympy.Array(0), sympy.Array(sympy.Symbol("x"))]
    result = [(a.shape, len(a), len(list(a))) for a in arrays]
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
