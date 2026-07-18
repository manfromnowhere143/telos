import sympy
from sympy import geometry as ge

def test():
    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)
    
    scalars = [
        sympy.sympify(2.0),
        sympy.sympify(3),
        sympy.Symbol('t')
    ]
    
    for s in scalars:
        # According to the issue, multiplying Point by a scalar works on the right,
        # but multiplying a sympy number by a Point on the right would fail during addition.
        # Both should evaluate to the same geometry result without exception.
        res1 = point1 + point2 * s
        res2 = point1 + s * point2
        
        if res1 != res2:
            return ('FAIL', f'Addition commutativity failed for scalar {s}')
            
        if not isinstance(res2, ge.Point):
            return ('FAIL', f'Result is not a Point for scalar {s}')
            
    return ('PASS',)

if __name__ == '__main__':
    try:
        result = test()
        print(f"RESULT={result!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")
