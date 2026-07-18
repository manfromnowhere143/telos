import sympy
from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    v = 2 * N.x - 3 * N.y + 5 * N.z

    assert 0 + v == v, "right zero addition"
    assert v + 0 == v, "left zero addition"
    assert sum([v, 0, -v, v]) == v, "sum with scalar zeros"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
