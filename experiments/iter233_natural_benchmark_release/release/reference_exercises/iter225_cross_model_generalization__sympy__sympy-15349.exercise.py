try:
    from sympy import Quaternion, cos, pi, sin, symbols, trigsimp

    x = symbols("x", real=True)
    symbolic = Quaternion(cos(x/2), sin(x/2), 0, 0).to_rotation_matrix()
    numeric = Quaternion(cos(pi/4), sin(pi/4), 0, 0).to_rotation_matrix()
    result = (
        tuple(trigsimp(symbolic[i, j]) for i, j in ((1, 1), (1, 2), (2, 1), (2, 2))),
        tuple(trigsimp(numeric[i, j]) for i, j in ((1, 1), (1, 2), (2, 1), (2, 2))),
    )
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
