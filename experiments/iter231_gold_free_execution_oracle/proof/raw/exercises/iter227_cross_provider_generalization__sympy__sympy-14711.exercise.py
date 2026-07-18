from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame('N')
    zero = 0 * N.x
    result = (
        sum([N.x, zero]),
        N.x + 0,
        0 + N.x,
        N.x + zero,
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
