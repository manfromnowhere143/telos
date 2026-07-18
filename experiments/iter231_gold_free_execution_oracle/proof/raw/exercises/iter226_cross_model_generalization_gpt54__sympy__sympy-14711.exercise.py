from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    results = (
        sum([N.x, 0 * N.x]),
        N.x + 0,
        0 + N.x,
        sum([N.x]),
    )
    print("RESULT=" + repr(tuple(map(repr, results))))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
