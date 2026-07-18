import sympy
from sympy import geometry as ge

try:
    cases = []
    for origin, point, factor in (
        (ge.Point(0, 0), ge.Point(1, 1), sympy.sympify(2.0)),
        (ge.Point(0, 0, 0), ge.Point(1, 1, 1), sympy.sympify(2.0)),
        (ge.Point(0, 0), ge.Point(1, 1), sympy.Symbol("k")),
    ):
        right = origin + point * factor
        left = origin + factor * point
        cases.append((right, left, right == left))
    print("RESULT=" + repr(tuple(cases)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
