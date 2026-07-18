import sympy

try:
    q = sympy.Quaternion(
        sympy.Rational(1, 2),
        sympy.Rational(1, 2),
        sympy.Rational(1, 2),
        sympy.Rational(1, 2),
    )
    rotation = q.to_rotation_matrix()
    expected = sympy.Matrix([
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0],
    ])

    if rotation != expected:
        raise AssertionError("wrong rotation orientation")
    if rotation.T * rotation != sympy.eye(3):
        raise AssertionError("rotation is not orthogonal")
    if rotation.det() != 1:
        raise AssertionError("rotation determinant")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc)
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
