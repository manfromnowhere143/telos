import sympy

try:
    p = sympy.IndexedBase("p")
    i, j = sympy.symbols("i j", integer=True)
    rendered = sympy.pycode(p[i, j])
    assert rendered == "p[i, j]", rendered
    assert "Not supported" not in rendered, rendered
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "indexed printing assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
