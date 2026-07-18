try:
    from sympy.physics.vector import ReferenceFrame, Vector
    from sympy import symbols

    N = ReferenceFrame('N')

    # sum() starts with integer 0 and adds vectors
    result = sum([N.x, (0 * N.x)])
    assert result == N.x, f"sum gave {result}"

    # 0 + Vector should work (radd)
    r2 = 0 + N.x
    assert r2 == N.x, f"0+N.x gave {r2}"

    # Vector + 0 should work
    r3 = N.x + 0
    assert r3 == N.x, f"N.x+0 gave {r3}"

    # sum of multiple vectors
    r4 = sum([N.x, N.y, N.z])
    assert r4 == N.x + N.y + N.z, f"sum gave {r4}"

    # 0*N.x should be the zero vector, and adding preserves the other
    zero_vec = 0 * N.x
    r5 = zero_vec + N.y
    assert r5 == N.y, f"zerovec+N.y gave {r5}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
