import sympy

try:
    q = sympy.Quaternion(sympy.cos(sympy.pi / 4), sympy.sin(sympy.pi / 4), 0, 0)
    rotation = q.to_rotation_matrix()

    y_axis = sympy.Matrix([0, 1, 0])
    z_axis = sympy.Matrix([0, 0, 1])

    assert rotation * y_axis == z_axis, "positive x rotation must send y to z"
    assert rotation * z_axis == -y_axis, "positive x rotation must send z to -y"
    assert rotation.det() == 1, "rotation matrix must have determinant one"
except AssertionError as exc:
    detail = str(exc)
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
