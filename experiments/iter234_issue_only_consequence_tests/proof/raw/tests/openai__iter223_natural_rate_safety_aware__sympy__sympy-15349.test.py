import sympy

try:
    h = sympy.sqrt(2) / 2
    cases = [
        (
            sympy.Quaternion(h, h, 0, 0),
            sympy.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]]),
            "x-axis",
        ),
        (
            sympy.Quaternion(h, 0, h, 0),
            sympy.Matrix([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),
            "y-axis",
        ),
        (
            sympy.Quaternion(h, 0, 0, h),
            sympy.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]]),
            "z-axis",
        ),
    ]
    for quaternion, expected, name in cases:
        if quaternion.to_rotation_matrix() != expected:
            raise AssertionError(name)
    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "rotation"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
