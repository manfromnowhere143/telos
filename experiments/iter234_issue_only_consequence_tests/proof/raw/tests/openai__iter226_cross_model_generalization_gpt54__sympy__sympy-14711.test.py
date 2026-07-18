import sympy
from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    v = 2 * N.x - 3 * N.y
    expected = v + N.z

    if 0 + v != v:
        raise AssertionError("left integer zero")
    if v + 0 != v:
        raise AssertionError("right integer zero")
    if sympy.S.Zero + v != v or v + sympy.S.Zero != v:
        raise AssertionError("SymPy zero")
    if sum([v, 0, N.z]) != expected:
        raise AssertionError("sum internal zero")
    if sum([v, sympy.S.Zero, N.z]) != expected:
        raise AssertionError("sum SymPy zero")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc)
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
