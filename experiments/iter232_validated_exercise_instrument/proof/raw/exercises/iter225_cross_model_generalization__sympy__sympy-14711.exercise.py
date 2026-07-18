from sympy.physics.vector import ReferenceFrame

try:
    N = ReferenceFrame("N")
    zero_vector = 0 * N.x
    result = (
        sum([N.x, zero_vector]),
        N.x + 0,
        0 + N.x,
        sum([N.x]),
        sum([zero_vector, N.x]),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
