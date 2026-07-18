from sympy import S
from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    v = 3*N.x - 2*N.y

    assert v + 0 == v
    assert v + S.Zero == v
    assert 0 + v == v
    assert S.Zero + v == v

    total = sum(component for component in (N.x, N.y, -N.x, 0*N.z))
    assert total == N.y

    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    detail = "zero is not a vector additive identity"
    print(f"RESULT={('FAIL', detail)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
