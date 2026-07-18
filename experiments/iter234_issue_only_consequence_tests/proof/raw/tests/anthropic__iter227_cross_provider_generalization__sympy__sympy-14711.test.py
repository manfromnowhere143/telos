try:
    from sympy.physics.vector import ReferenceFrame, Vector
    N = ReferenceFrame('N')

    result = sum([N.x, (0 * N.x)])
    assert result == N.x, f"sum gave {result}"

    # 0*N.x should be the zero vector
    zero_vec = 0 * N.x
    assert zero_vec == Vector(0), f"0*N.x gave {zero_vec}"

    # Adding zero on either side
    assert N.x + zero_vec == N.x, "N.x + zero failed"
    assert zero_vec + N.x == N.x, "zero + N.x failed"

    # sum with default start of int 0
    assert sum([N.x, N.y]) == N.x + N.y, "sum of two vectors failed"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
