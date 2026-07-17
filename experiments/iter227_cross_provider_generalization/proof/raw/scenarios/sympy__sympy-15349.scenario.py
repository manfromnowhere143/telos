from sympy import Integer, Symbol
from sympy.algebras.quaternion import Quaternion

class Probe(Symbol):
    hits = 0

    def __mul__(self, other):
        if isinstance(other, Probe) and self.name == "b" and other.name == "c":
            Probe.hits += 1
            return Integer(Probe.hits)
        return super().__mul__(other)

b = Probe("b")
c = Probe("c")
matrix = Quaternion(1, b, c, 0).to_rotation_matrix()
print("RESULT=" + repr(matrix[1, 0]))
