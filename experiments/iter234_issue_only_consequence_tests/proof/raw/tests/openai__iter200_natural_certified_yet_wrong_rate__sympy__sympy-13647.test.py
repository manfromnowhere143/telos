import sympy as sm

try:
    source = sm.Matrix(4, 6, lambda r, c: 10*r + c)
    inserted = sm.Matrix(4, 3, lambda r, c: 100 + 10*r + c)

    result = source.col_insert(4, inserted)
    expected = sm.Matrix([
        [source[r, c] for c in range(4)] +
        [inserted[r, c] for c in range(3)] +
        [source[r, c] for c in range(4, 6)]
        for r in range(4)
    ])

    if result != expected:
        raise AssertionError("column insertion misaligns trailing columns")
    if result.shape != (4, 9):
        raise AssertionError("wrong result shape")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
