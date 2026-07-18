import sympy

try:
    a, b = sympy.symbols("a b", integer=True)
    equation = a**4 + b**4 - 17
    expected = {
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    }

    first = sympy.diophantine(equation, syms=(a, b), permute=True)
    second = sympy.diophantine(equation, syms=(b, a), permute=True)

    if first != expected or second != expected:
        raise AssertionError("permuted fourth-power solutions incomplete")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
else:
    print(f"RESULT={('PASS',)!r}")
