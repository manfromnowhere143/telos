import sympy
from sympy import geometry as ge

try:
    factor = sympy.sympify(2.0)
    cases = []
    for point1, point2 in (
        (ge.Point(0, 0), ge.Point(1, 1)),
        (ge.Point(0, 0, 0), ge.Point(1, 1, 1)),
    ):
        right = point1 + point2 * factor
        left = point1 + factor * point2
        cases.append((repr(right), repr(left), right == left))
    print("RESULT=" + repr(cases))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
