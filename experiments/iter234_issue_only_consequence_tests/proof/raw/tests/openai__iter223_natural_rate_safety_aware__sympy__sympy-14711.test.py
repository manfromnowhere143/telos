import sympy
from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    terms = (v for v in (N.x, 2 * N.y, -N.x, 0 * N.z))
    total = sum(terms)

    if total != 2 * N.y:
        raise AssertionError("sum with initial zero")
    if N.x + 0 != N.x or 0 + N.x != N.x:
        raise AssertionError("zero vector addition")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    detail = str(exc) or "assertion"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
