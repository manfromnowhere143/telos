try:
    from sympy import Quaternion, cos, pi, sin, symbols, trigsimp

    x = symbols("x", real=True)
    q_symbolic = Quaternion(cos(x/2), sin(x/2), 0, 0)
    q_numeric = Quaternion(cos(pi/4), sin(pi/4), 0, 0)

    symbolic = tuple(tuple(trigsimp(q_symbolic.to_rotation_matrix()[i, j])
                           for j in range(3)) for i in range(3))
    numeric = tuple(tuple(trigsimp(q_numeric.to_rotation_matrix()[i, j])
                          for j in range(3)) for i in range(3))
    print("RESULT=" + repr((symbolic, numeric)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
