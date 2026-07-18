import sympy

try:
    x = sympy.Symbol("x")
    scalar = x + 2
    a = sympy.Array(scalar)
    elements = list(a)

    if a.shape != ():
        raise AssertionError("not rank zero")
    if len(a) != 1:
        raise AssertionError("scalar length")
    if len(a) != len(elements):
        raise AssertionError("length iterator mismatch")
    if elements != [scalar]:
        raise AssertionError("scalar iteration")

    print(f"RESULT={('PASS',)!r}")
except AssertionError as exc:
    print(f"RESULT={('FAIL', str(exc))!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
