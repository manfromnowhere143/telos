try:
    from sympy import Symbol, srepr

    x = Symbol("x")
    y = Symbol("y")
    output = srepr({x: y})
    print(f"RESULT={output!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
