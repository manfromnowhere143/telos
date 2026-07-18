import sympy
from sympy import geometry as ge

try:
    results = []
    for base, point in (
        (ge.Point(0, 0), ge.Point(1, 1)),
        (ge.Point3D(0, 0, 0), ge.Point3D(1, 1, 1)),
    ):
        factor = sympy.sympify(2.0)
        left = factor * point
        right = point * factor
        results.append((
            repr(left),
            repr(right),
            left == right,
            repr(base + left),
            repr(base + right),
            (base + left) == (base + right),
        ))
    print("RESULT=" + repr(tuple(results)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
