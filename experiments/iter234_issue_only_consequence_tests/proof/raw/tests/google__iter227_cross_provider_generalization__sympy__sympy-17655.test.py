import sympy
from sympy import geometry as ge

def test():
    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)
    
    val = sympy.sympify(2.0)
    
    # Left multiplication should yield a Point, just like right multiplication
    mul1 = point2 * val
    mul2 = val * point2
    
    if not isinstance(mul2, ge.Point):
        return ('FAIL', f"val * point2 returned {type(mul2).__name__}, expected a Point")
        
    if mul1 != mul2:
        return ('FAIL', "Left and right multiplication yield different results")
        
    # The specific issue: addition should work without raising an exception
    # (previously val * point2 evaluated to a Mul object causing GeometryError)
    res1 = point1 + point2 * val
    res2 = point1 + val * point2
    
    if res1 != res2:
        return ('FAIL', "Addition results differ for left vs right multiplication")
        
    return ('PASS',)

try:
    print(f"RESULT={test()!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
