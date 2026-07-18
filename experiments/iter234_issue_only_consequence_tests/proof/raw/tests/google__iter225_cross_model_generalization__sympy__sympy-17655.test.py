import sympy
from sympy import geometry as ge

def run_tests():
    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)
    val = sympy.sympify(2.0)

    try:
        # The line that originally worked
        res1 = point1 + point2 * val
    except Exception as e:
        return ('FAIL', f'Right multiplication failed: {e}')

    try:
        # The line that originally failed
        res2 = point1 + val * point2
    except Exception as e:
        return ('FAIL', f'Left multiplication failed: {e}')

    if res1 != res2:
        return ('FAIL', f'Results differ: {res1} != {res2}')
        
    # Ensure left-multiplication directly yields a Point (not a Mul object)
    prod_left = val * point2
    if not isinstance(prod_left, ge.Point):
        return ('FAIL', f'val * point2 yielded {type(prod_left).__name__}, expected Point')

    # Also verify with 3D points and integers
    p3_1 = ge.Point3D(0, 0, 0)
    p3_2 = ge.Point3D(1, 2, 3)
    val_int = 3
    
    try:
        res3 = p3_1 + val_int * p3_2
        res4 = p3_1 + p3_2 * val_int
        if res3 != res4:
            return ('FAIL', 'Results differ for 3D points and int')
    except Exception as e:
        return ('FAIL', f'3D test failed: {e}')

    return ('PASS',)

try:
    result = run_tests()
    print(f"RESULT={result!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
