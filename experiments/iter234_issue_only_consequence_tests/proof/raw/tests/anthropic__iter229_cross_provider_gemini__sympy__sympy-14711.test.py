try:
    from sympy.physics.vector import ReferenceFrame, Vector
    from sympy import symbols

    N = ReferenceFrame('N')

    # The core issue: sum() with a zero vector
    result = sum([N.x, (0 * N.x)])
    assert result == N.x, f"sum result wrong: {result}"

    # 0 + vector via sum starts with integer 0
    result2 = sum([N.x, N.y])
    assert result2 == N.x + N.y, f"sum of two vectors wrong: {result2}"

    # explicit 0 + Vector
    result3 = 0 + N.x
    assert result3 == N.x, f"0 + N.x wrong: {result3}"

    # Vector + 0
    result4 = N.x + 0
    assert result4 == N.x, f"N.x + 0 wrong: {result4}"

    # 0 * N.x is a zero vector; adding it changes nothing
    z = 0 * N.x
    result5 = N.z + z
    assert result5 == N.z, f"N.z + zerovector wrong: {result5}"

    # sum over several including zeros
    result6 = sum([N.x, 0 * N.y, N.y, 0 * N.z])
    assert result6 == N.x + N.y, f"multi sum wrong: {result6}"

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
