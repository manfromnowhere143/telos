from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame("N")
v = N.x
print("RESULT=" + repr(hash(v + 0) == hash(v)))
