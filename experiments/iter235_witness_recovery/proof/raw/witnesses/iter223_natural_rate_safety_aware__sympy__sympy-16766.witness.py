try:
    import sympy

    if not hasattr(sympy, "pycode"):
        raise AttributeError("pycode")

    class Args:
        def __getitem__(self, key):
            if key == 0:
                return "p"
            if isinstance(key, slice):
                return (0,)
            raise IndexError(key)

        def __iter__(self):
            return iter(("q", 1))

    class Indexed:
        def __init__(self):
            self.args = Args()

    result = sympy.pycode(Indexed())
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print(f"RESULT={result!r}")
