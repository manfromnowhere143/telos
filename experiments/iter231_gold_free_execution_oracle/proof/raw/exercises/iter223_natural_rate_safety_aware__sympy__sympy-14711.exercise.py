from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    result = (
        sum([N.x, 0 * N.x]),
        N.x + 0,
        0 + N.x,
        sum([N.x]),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
