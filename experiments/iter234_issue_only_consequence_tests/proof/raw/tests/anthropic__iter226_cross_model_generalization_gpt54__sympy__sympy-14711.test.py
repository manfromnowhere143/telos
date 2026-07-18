try:
    from sympy.physics.vector import ReferenceFrame, Vector
    from sympy import symbols

    N = ReferenceFrame('N')

    # The core issue: sum() starts with int 0 and adds vectors
    result = sum([N.x, (0 * N.x)])
    assert result == N.x, f"sum gave {result}"

    # Direct: adding integer 0 to a vector should work
    r2 = N.x + 0
    assert r2 == N.x, f"N.x + 0 = {r2}"

    r3 = 0 + N.x
    assert r3 == N.x, f"0 + N.x = {r3}"

    # sum of a list of vectors
    r4 = sum([N.x, N.y, N.z])
    assert r4 == N.x + N.y + N.z, f"sum vectors = {r4}"

    # subtracting zero
    r5 = N.x - 0
    assert r5 == N.x, f"N.x - 0 = {r5}"

    # zero vector is the Vector(0) not int
    z = 0 * N.x
    assert isinstance(z, Vector), "0*N.x not a Vector"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
