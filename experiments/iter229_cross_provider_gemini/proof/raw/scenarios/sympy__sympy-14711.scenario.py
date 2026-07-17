from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame("N")
v = N.x
v.__hash__()
print("RESULT=" + repr((v + 0) is v))
