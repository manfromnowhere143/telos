from sympy import geometry as ge
import sympy

try:
    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)

    a = point1 + point2 * sympy.sympify(2.0)
    b = point1 + sympy.sympify(2.0) * point2

    if a != b:
        print(f"RESULT={('FAIL', 'commuted results differ')!r}")
    elif b != ge.Point(2.0, 2.0):
        print(f"RESULT={('FAIL', 'wrong value ' + str(b))!r}")
    else:
        # 3D check too
        p3a = ge.Point(0, 0, 0)
        p3b = ge.Point(1, 2, 3)
        r1 = p3a + p3b * sympy.sympify(2)
        r2 = p3a + sympy.sympify(2) * p3b
        if r1 != r2:
            print(f"RESULT={('FAIL', '3D commuted differ')!r}")
        elif r2 != ge.Point(2, 4, 6):
            print(f"RESULT={('FAIL', 'wrong 3D ' + str(r2))!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
