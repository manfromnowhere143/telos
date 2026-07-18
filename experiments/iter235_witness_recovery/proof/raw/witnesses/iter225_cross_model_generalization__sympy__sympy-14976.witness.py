try:
    from sympy import Rational
    from sympy.printing.pycode import MpmathPrinter

    printer = MpmathPrinter()
    if hasattr(printer, "doprint"):
        result = printer.doprint(Rational(232, 3))
    else:
        result = ("ERROR", "AttributeError")
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
