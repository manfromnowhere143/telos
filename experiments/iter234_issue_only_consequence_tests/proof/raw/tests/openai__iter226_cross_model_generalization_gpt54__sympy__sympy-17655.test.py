import sympy

try:
    ge = sympy.geometry

    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)
    scalar = sympy.sympify(2.0)

    left_2d = point1 + scalar * point2
    right_2d = point1 + point2 * scalar
    expected_2d = ge.Point(scalar, scalar)
    if left_2d != expected_2d or right_2d != expected_2d:
        raise AssertionError("2d float scaling")

    anchor = ge.Point3D(3, -5, 7)
    vector = ge.Point3D(-2, 4, 1)
    scale = sympy.sympify(-1.5)
    expected_3d = ge.Point3D(
        anchor.x + scale * vector.x,
        anchor.y + scale * vector.y,
        anchor.z + scale * vector.z,
    )
    left_3d = anchor + scale * vector
    right_3d = anchor + vector * scale
    if left_3d != expected_3d or right_3d != expected_3d:
        raise AssertionError("3d float scaling")

except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
