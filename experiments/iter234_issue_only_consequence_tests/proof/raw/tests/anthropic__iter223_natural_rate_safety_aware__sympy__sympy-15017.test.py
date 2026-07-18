try:
    import sympy

    a = sympy.Array(3)
    assert len(a) == 1, f"len rank-0 = {len(a)}"
    assert len(list(a)) == 1, f"iter len = {len(list(a))}"
    assert len(a) == len(list(a)), "len mismatch with iterator"

    # Ensure normal arrays still behave correctly
    b = sympy.Array([1, 2, 3])
    assert len(b) == 3, f"len 1d = {len(b)}"
    assert len(b) == len(list(b)), "1d len mismatch"

    c = sympy.Array([[1, 2], [3, 4]])
    assert len(c) == 4, f"len 2d = {len(c)}"

    # MutableDenseNDimArray rank-0
    m = sympy.MutableDenseNDimArray(5)
    assert len(m) == 1, f"mutable rank-0 len = {len(m)}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
