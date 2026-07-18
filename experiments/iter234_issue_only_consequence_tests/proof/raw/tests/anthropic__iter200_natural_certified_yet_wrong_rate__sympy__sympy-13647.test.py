try:
    import sympy as sm

    M = sm.eye(6)
    V = 2 * sm.ones(6, 2)
    R = M.col_insert(3, V)

    expected = sm.Matrix([
        [1, 0, 0, 2, 2, 0, 0, 0],
        [0, 1, 0, 2, 2, 0, 0, 0],
        [0, 0, 1, 2, 2, 0, 0, 0],
        [0, 0, 0, 2, 2, 1, 0, 0],
        [0, 0, 0, 2, 2, 0, 1, 0],
        [0, 0, 0, 2, 2, 0, 0, 1],
    ])

    if R.shape != (6, 8):
        print(f"RESULT={('FAIL', 'shape ' + str(R.shape))!r}")
    elif R != expected:
        print(f"RESULT={('FAIL', 'wrong result ' + str(R.tolist()))!r}")
    else:
        # extra check: inserting at 0 and at end
        R0 = M.col_insert(0, V)
        ok0 = all(R0[i, 0] == 2 and R0[i, 1] == 2 for i in range(6))
        Rend = M.col_insert(6, V)
        okend = all(Rend[i, 6] == 2 and Rend[i, 7] == 2 for i in range(6))
        # identity part in R0 shifted right by 2
        okid = all(R0[i, i + 2] == 1 for i in range(6))
        if ok0 and okend and okid:
            print(f"RESULT={('PASS',)!r}")
        else:
            print(f"RESULT={('FAIL', 'edge insert')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
