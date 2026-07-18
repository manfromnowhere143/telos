try:
    from sympy import IndexedBase, symbols
    from sympy.printing.pycode import pycode

    p = IndexedBase("p")
    i, j = symbols("i j")

    out0 = pycode(p[0])
    assert out0 == "p[0]", f"single index: {out0!r}"
    assert "Not supported" not in out0, "warning present for p[0]"

    out1 = pycode(p[i])
    assert out1 == "p[i]", f"symbol index: {out1!r}"
    assert "Not supported" not in out1, "warning present for p[i]"

    out2 = pycode(p[i, j])
    assert out2 == "p[i, j]", f"multi index: {out2!r}"
    assert "Not supported" not in out2, "warning present for p[i, j]"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
