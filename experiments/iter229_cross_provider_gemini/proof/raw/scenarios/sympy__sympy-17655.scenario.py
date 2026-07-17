from sympy.geometry import Point2D

class DerivedPoint(Point2D):
    def __mul__(self, factor):
        return "overridden"

point = DerivedPoint(1, 2)
print("RESULT=" + repr(2 * point))
