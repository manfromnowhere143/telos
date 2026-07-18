from sympy.physics.vector import ReferenceFrame
from sympy import S

try:
    N = ReferenceFrame('N')
    v = N.x + 2 * N.y
    
    # Test addition with integer 0
    if v + 0 != v:
        raise AssertionError("v + 0 != v")
    if 0 + v != v:
        raise AssertionError("0 + v != v")
        
    # Test addition with S.Zero
    if v + S.Zero != v:
        raise AssertionError("v + S.Zero != v")
    if S.Zero + v != v:
        raise AssertionError("S.Zero + v != v")

    # Test subtraction with integer 0
    if v - 0 != v:
        raise AssertionError("v - 0 != v")
    if 0 - v != -v:
        raise AssertionError("0 - v != -v")
        
    # Test subtraction with S.Zero
    if v - S.Zero != v:
        raise AssertionError("v - S.Zero != v")
    if S.Zero - v != -v:
        raise AssertionError("S.Zero - v != -v")

    # Test sum over mixed representations of zero, 
    # relying on Python's built-in sum() starting with an integer 0
    if sum([v, 0 * N.x, S.Zero]) != v:
        raise AssertionError("sum(...) with mixed zeroes failed")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
