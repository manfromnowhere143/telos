from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame("N")
v = 2 * N.x
h = (v + 0).__hash__()
print("RESULT=" + repr(((v + 0) is v, type(h).__name__)))
