try:
    from sympy.physics.vector import ReferenceFrame

    N = ReferenceFrame('N')
    zero_vector = 0 * N.x
    results = (
        sum([N.x, zero_vector]),
        sum([zero_vector, N.x]),
        N.x + 0,
        0 + N.x,
    )
    print("RESULT=" + repr(tuple(map(str, results))))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
