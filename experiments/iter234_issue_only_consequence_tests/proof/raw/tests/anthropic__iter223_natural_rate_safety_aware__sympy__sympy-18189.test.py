try:
    from sympy import symbols
    from sympy.solvers.diophantine import diophantine

    m, n = symbols('m n', integer=True)
    expr = n**4 + m**4 - 2**4 - 3**4

    res_mn = diophantine(expr, syms=(m, n), permute=True)
    res_nm = diophantine(expr, syms=(n, m), permute=True)

    expected = {(-3, -2), (-3, 2), (-2, -3), (-2, 3),
                (2, -3), (2, 3), (3, -2), (3, 2)}

    if res_mn != expected:
        print(f"RESULT={('FAIL', 'syms=(m,n) got ' + str(res_mn))!r}")
    elif res_nm != expected:
        print(f"RESULT={('FAIL', 'syms=(n,m) got ' + str(res_nm))!r}")
    elif res_mn != res_nm:
        print(f"RESULT={('FAIL', 'order-dependent results')!r}")
    else:
        print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
