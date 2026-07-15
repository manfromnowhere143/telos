from sympy import FiniteSet, Symbol
from sympy.sets.sets import Set


class NumericTruthSet(Set):
    def contains(self, other):
        return 1


result = NumericTruthSet()._complement(FiniteSet(Symbol("x")))
print("RESULT=" + repr(result))
