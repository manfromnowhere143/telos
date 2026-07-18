try:
    import sympy as sm

    M = sm.eye(6)
    V = 2 * sm.ones(6, 2)
    R = M.col_insert(3, V)
    result = tuple(tuple(R[i, j] for j in range(R.cols)) for i in range(R.rows))
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
