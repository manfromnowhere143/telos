try:
    from sympy import IndexedBase, symbols
    from sympy.printing.pycode import pycode

    p = IndexedBase("p")
    out = pycode(p[0])
    # Should not contain the "Not supported" warning
    assert "Not supported" not in out, "warning still present"
    assert "Indexed" not in out, "Indexed comment present"
    assert out == "p[0]", f"got {out!r}"

    i, j = symbols("i j")
    out2 = pycode(p[i, j])
    assert "Not supported" not in out2, "warning in multi-index"
    assert out2 == "p[i, j]", f"got {out2!r}"

    A = IndexedBase("A")
    out3 = pycode(A[i])
    assert out3 == "A[i]", f"got {out3!r}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
