from sympy.geometry import Point

class DerivedPoint(Point):
    def __mul__(self, factor):
        return "override"

point = DerivedPoint(0, 0)
print("RESULT=" + repr(2 * point))
