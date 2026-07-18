import sympy
from sympy import geometry as ge

try:
    scalar = sympy.sympify(2.0)
    point = ge.Point(1, -2, 3)
    offset = ge.Point(-4, 5, 6)

    left_product = scalar * point
    right_product = point * scalar

    if not isinstance(left_product, ge.Point):
        raise AssertionError("left product is not Point")
    if left_product != right_product:
        raise AssertionError("scalar multiplication differs")
    if (left_product.x, left_product.y, left_product.z) != (
        scalar * point.x,
        scalar * point.y,
        scalar * point.z,
    ):
        raise AssertionError("scaled coordinates incorrect")
    if offset + left_product != offset + right_product:
        raise AssertionError("addition results differ")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
