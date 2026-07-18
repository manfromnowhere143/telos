try:
    from sympy import IndexedBase, symbols
    from sympy.printing.pycode import pycode

    p = IndexedBase("p")
    i, j = symbols("i j")
    result = (pycode(p[0]), pycode(p[i, j]), pycode(p[i + 1]))
    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
