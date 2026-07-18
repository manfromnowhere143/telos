try:
    from sympy.physics.vector import ReferenceFrame
    from sympy import S

    N = ReferenceFrame('N')
    
    if (N.x + 0) != N.x:
        print(f"RESULT={('FAIL', 'N.x + 0 != N.x')!r}")
    elif (0 + N.x) != N.x:
        print(f"RESULT={('FAIL', '0 + N.x != N.x')!r}")
    elif (N.x - 0) != N.x:
        print(f"RESULT={('FAIL', 'N.x - 0 != N.x')!r}")
    elif (0 - N.x) != -N.x:
        print(f"RESULT={('FAIL', '0 - N.x != -N.x')!r}")
    elif sum([N.x, 0 * N.x]) != N.x:
        print(f"RESULT={('FAIL', 'sum([N.x, 0 * N.x]) != N.x')!r}")
    elif (N.x + S.Zero) != N.x:
        print(f"RESULT={('FAIL', 'N.x + S.Zero != N.x')!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
