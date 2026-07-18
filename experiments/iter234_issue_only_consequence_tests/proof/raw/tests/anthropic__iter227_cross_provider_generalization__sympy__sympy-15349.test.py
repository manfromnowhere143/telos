try:
    from sympy import symbols, cos, sin, trigsimp, Quaternion, Matrix

    x = symbols('x')
    q = Quaternion(cos(x/2), sin(x/2), 0, 0)
    M = trigsimp(q.to_rotation_matrix())

    # Rotation about x-axis by angle x:
    expected = Matrix([
        [1,      0,       0],
        [0, cos(x), -sin(x)],
        [0, sin(x),  cos(x)]])

    diff = trigsimp(M - expected)
    if diff != Matrix.zeros(3, 3):
        print(f"RESULT={('FAIL', str(M))!r}")
    else:
        # Verify orthogonality (proper rotation)
        prod = trigsimp(M * M.T)
        if prod != Matrix.eye(3):
            print(f"RESULT={('FAIL', 'not orthogonal')!r}")
        elif trigsimp(M.det()) != 1:
            print(f"RESULT={('FAIL', 'det!=1')!r}")
        else:
            print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
