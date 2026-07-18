import sympy
from sympy import geometry as ge

try:
    scale = sympy.sympify(2.0)

    p2 = ge.Point(-2, 3)
    offset2 = ge.Point(4, -1)
    left2 = offset2 + scale * p2
    right2 = offset2 + p2 * scale
    if left2 != right2:
        raise AssertionError("2D scalar order differs")
    if left2 != ge.Point(0, 5):
        raise AssertionError("2D result is incorrect")

    p3 = ge.Point(3, -2, 1)
    offset3 = ge.Point(-1, 2, 4)
    left3 = offset3 + scale * p3
    right3 = offset3 + p3 * scale
    if left3 != right3:
        raise AssertionError("3D scalar order differs")
    if left3 != ge.Point(5, -2, 6):
        raise AssertionError("3D result is incorrect")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion failed"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
