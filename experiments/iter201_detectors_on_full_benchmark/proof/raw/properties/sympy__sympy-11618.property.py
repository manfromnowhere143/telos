from sympy import Integer
from sympy.geometry import Point2D, Point3D

try:
    p2 = Point2D(-3, 4)
    p3 = Point3D(1, -2, 12)
    result = p2.distance(p3)
    print("PROP_PASS" if result == Integer(14) else "PROP_FAIL")
except Exception:
    print("PROP_FAIL")
