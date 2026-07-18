try:
    from sympy import symbols, cos, sin, trigsimp, Quaternion, Matrix

    x = symbols('x')
    q = Quaternion(cos(x/2), sin(x/2), 0, 0)
    R = trigsimp(q.to_rotation_matrix())

    expected = Matrix([
        [1,      0,       0],
        [0, cos(x), -sin(x)],
        [0, sin(x),  cos(x)]])

    diff = trigsimp(R - expected)
    if diff != Matrix.zeros(3, 3):
        print(f"RESULT={('FAIL', 'rotation matrix mismatch: ' + str(R))!r}")
    else:
        # verify it is a proper rotation (determinant 1, orthogonal)
        det = trigsimp(R.det())
        if trigsimp(det - 1) != 0:
            print(f"RESULT={('FAIL', 'det not 1: ' + str(det))!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
