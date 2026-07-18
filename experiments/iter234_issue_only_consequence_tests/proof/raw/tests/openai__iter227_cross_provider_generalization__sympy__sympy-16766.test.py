import sympy

try:
    p = sympy.IndexedBase("p")
    i, j = sympy.symbols("i j")
    code = sympy.pycode(p[i, j + 1])

    if code != "p[i, j + 1]":
        raise AssertionError("multidimensional Indexed code is incorrect")
    if "Not supported" in code or "#" in code:
        raise AssertionError("Indexed emitted an unsupported warning")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc)
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
