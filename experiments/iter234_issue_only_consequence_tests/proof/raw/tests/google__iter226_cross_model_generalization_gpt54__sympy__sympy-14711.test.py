def test():
    from sympy.physics.vector import ReferenceFrame
    from sympy import S
    
    N = ReferenceFrame('N')
    
    # Test the specific sum case from the issue, which starts with 0 (from sum's default start)
    # and evaluates 0 + N.x + (0 * N.x)
    res1 = sum([N.x, 0 * N.x])
    if res1 != N.x:
        return ('FAIL', 'sum([N.x, 0*N.x]) did not equal N.x')
        
    # Additional edge cases checking direct scalar addition with 0
    if (N.x + 0) != N.x:
        return ('FAIL', 'N.x + 0 != N.x')
        
    if (0 + N.y) != N.y:
        return ('FAIL', '0 + N.y != N.y')
        
    # Check interaction with SymPy's S.Zero
    if (N.z + S.Zero) != N.z:
        return ('FAIL', 'N.z + S.Zero != N.z')
        
    if (S.Zero + N.x) != N.x:
        return ('FAIL', 'S.Zero + N.x != N.x')

    return ('PASS',)

try:
    print(f"RESULT={test()!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
