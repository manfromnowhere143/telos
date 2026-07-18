import sympy
from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame('N')
    
    # Test adding and subtracting scalar 0 with a vector.
    # This ensures that operations like `0 + N.x` do not raise a TypeError.
    assert (0 + N.x) == N.x, "0 + N.x did not evaluate to N.x"
    assert (N.x + 0) == N.x, "N.x + 0 did not evaluate to N.x"
    
    assert (0 - N.x) == -N.x, "0 - N.x did not evaluate to -N.x"
    assert (N.x - 0) == N.x, "N.x - 0 did not evaluate to N.x"
    
    # Test the exact issue's reproduction snippet.
    # `sum()` uses `0` as the default start value, making this effectively evaluate:
    # 0 + N.x + (0 * N.x)
    res = sum([N.x, 0 * N.x])
    assert res == N.x, "sum([N.x, 0 * N.x]) did not evaluate to N.x"
    
    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
