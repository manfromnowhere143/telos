from sympy import Integer, Symbol
from sympy.printing.pycode import PythonCodePrinter


class Args:
    def __getitem__(self, key):
        return (Symbol("p"), Integer(0))[key]

    def __iter__(self):
        return iter((Symbol("q"), Integer(1)))


class Indexed:
    args = Args()


result = PythonCodePrinter().doprint(Indexed())
print("RESULT={!r}".format(result))
