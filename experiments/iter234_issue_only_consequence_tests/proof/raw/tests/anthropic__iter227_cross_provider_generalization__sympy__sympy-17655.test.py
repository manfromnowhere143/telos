try:
    from sympy import geometry as ge
    import sympy

    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)

    left = point1 + point2 * sympy.sympify(2.0)
    right = point1 + sympy.sympify(2.0) * point2

    assert left == right, f"mismatch {left} vs {right}"
    assert right == ge.Point(2.0, 2.0), f"unexpected {right}"

    # 3D check too
    p3a = ge.Point(0, 0, 0)
    p3b = ge.Point(1, 2, 3)
    l3 = p3a + p3b * sympy.sympify(3)
    r3 = p3a + sympy.sympify(3) * p3b
    assert l3 == r3, f"3D mismatch {l3} vs {r3}"
    assert r3 == ge.Point(3, 6, 9), f"unexpected 3D {r3}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
