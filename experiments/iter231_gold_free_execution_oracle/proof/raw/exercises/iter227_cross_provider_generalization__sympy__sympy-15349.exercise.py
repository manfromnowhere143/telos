import sympy

try:
    x = sympy.symbols("x")
    h = x / 2
    quaternions = (
        sympy.Quaternion(sympy.cos(h), sympy.sin(h), 0, 0),
        sympy.Quaternion(sympy.cos(h), 0, sympy.sin(h), 0),
        sympy.Quaternion(sympy.cos(h), 0, 0, sympy.sin(h)),
    )
    result = tuple(
        tuple(sympy.trigsimp(q.to_rotation_matrix()[i, j])
              for i in range(3) for j in range(3))
        for q in quaternions
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
