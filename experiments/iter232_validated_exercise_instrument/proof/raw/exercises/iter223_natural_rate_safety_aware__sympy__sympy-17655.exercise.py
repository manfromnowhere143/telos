from sympy import geometry as ge, sympify

try:
    factor = sympify(2.0)
    cases = []
    for origin, point in (
        (ge.Point(0, 0), ge.Point(1, 1)),
        (ge.Point(0, 0, 0), ge.Point(1, 1, 1)),
    ):
        right = origin + point * factor
        left = origin + factor * point
        cases.append((repr(right), repr(left), right == left))
    print("RESULT=" + repr(tuple(cases)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
