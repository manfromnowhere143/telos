try:
    from sympy import symbols, cos, sin, trigsimp, Matrix, Quaternion

    x = symbols('x')
    q = Quaternion(cos(x/2), sin(x/2), 0, 0)
    M = trigsimp(q.to_rotation_matrix())

    expected = Matrix([
        [1, 0, 0],
        [0, cos(x), -sin(x)],
        [0, sin(x), cos(x)]])

    diff = trigsimp(M - expected)
    if diff != Matrix.zeros(3, 3):
        print(f"RESULT={('FAIL', 'rotation about x-axis wrong: '+str(M))!r}")
    else:
        # verify it's a proper rotation: R * R^T == I, det == 1
        RRt = trigsimp(M * M.T)
        if RRt != Matrix.eye(3):
            print(f"RESULT={('FAIL', 'not orthogonal: '+str(RRt))!r}")
        elif trigsimp(M.det()) != 1:
            print(f"RESULT={('FAIL', 'det not 1: '+str(M.det()))!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
