try:
    from sympy.physics.vector import ReferenceFrame, Vector
    N = ReferenceFrame('N')

    # sum() starts with int 0, so this exercises Vector.__radd__ with 0
    result = sum([N.x, (0 * N.x)])
    assert result == N.x, f"sum gave {result}"

    # direct add of int 0
    assert N.x + 0 == N.x, "N.x + 0 failed"
    assert 0 + N.x == N.x, "0 + N.x failed"

    # subtracting 0
    assert N.x - 0 == N.x, "N.x - 0 failed"

    # sum of several vectors including zero vector
    total = sum([N.x, N.y, 0 * N.z])
    assert total == N.x + N.y, f"sum many gave {total}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
