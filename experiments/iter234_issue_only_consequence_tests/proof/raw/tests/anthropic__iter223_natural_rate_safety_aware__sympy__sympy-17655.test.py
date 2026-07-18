try:
    from sympy import geometry as ge
    import sympy

    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)

    left = point1 + point2 * sympy.sympify(2.0)
    right = point1 + sympy.sympify(2.0) * point2

    assert left == right, f"mismatch {left} vs {right}"
    assert right == ge.Point(2.0, 2.0), f"unexpected {right}"

    # 3D check
    a = ge.Point(1, 2, 3)
    b = ge.Point(4, 5, 6)
    l3 = a + b * sympy.sympify(3)
    r3 = a + sympy.sympify(3) * b
    assert l3 == r3, f"3D mismatch {l3} vs {r3}"
    assert r3 == ge.Point(13, 17, 21), f"unexpected 3D {r3}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
