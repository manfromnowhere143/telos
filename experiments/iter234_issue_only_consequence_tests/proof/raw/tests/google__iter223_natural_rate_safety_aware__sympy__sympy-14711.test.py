try:
    from sympy.physics.vector import ReferenceFrame
    
    N = ReferenceFrame('N')
    
    # Test addition with scalar 0
    v1 = N.x + 0
    assert v1 == N.x, f"N.x + 0 expected {N.x}, got {v1}"
    
    v2 = 0 + N.x
    assert v2 == N.x, f"0 + N.x expected {N.x}, got {v2}"
    
    # Test subtraction with scalar 0
    v3 = N.x - 0
    assert v3 == N.x, f"N.x - 0 expected {N.x}, got {v3}"
    
    v4 = 0 - N.x
    assert v4 == -N.x, f"0 - N.x expected {-N.x}, got {v4}"
    
    # Test the exact reproducer from the issue
    s = sum([N.x, (0 * N.x)])
    assert s == N.x, f"sum([N.x, (0 * N.x)]) expected {N.x}, got {s}"
    
    print(f"RESULT={('PASS',)!r}")
except AssertionError as e:
    print(f"RESULT={('FAIL', str(e))!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
