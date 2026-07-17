from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame("N")
v = sum([N.x, 0 * N.x])
h = v.__hash__()
print("RESULT=" + repr((v == N.x, type(h).__name__)))
