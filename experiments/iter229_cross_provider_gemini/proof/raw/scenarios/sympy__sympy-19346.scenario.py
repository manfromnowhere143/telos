from sympy import Symbol
from sympy.printing.repr import ReprPrinter


class OrderedSet(set):
    def __init__(self, values, order):
        super().__init__(values)
        self._order = tuple(order)

    def __iter__(self):
        return iter(self._order)


a = Symbol("a")
b = Symbol("b")
value = OrderedSet([a, b], [b, a])

output = ReprPrinter().doprint(value)
print("RESULT=" + repr(output))
