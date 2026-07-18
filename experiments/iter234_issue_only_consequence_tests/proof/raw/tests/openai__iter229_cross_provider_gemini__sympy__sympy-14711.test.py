import sympy
from sympy.physics.vector import ReferenceFrame, Vector

try:
    N = ReferenceFrame("N")
    total = sum([N.x, 0, N.y, 0])
    assert isinstance(total, Vector)
    assert total == N.x + N.y
    assert 0 + N.x == N.x
    assert N.y + 0 == N.y
    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'zero scalar identity for vectors')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
