import sympy
from sympy import geometry as ge

def check_issue():
    point1 = ge.Point(0, 0)
    point2 = ge.Point(1, 1)
    
    # Test 1: Float as SymPy object (from issue description)
    num1 = sympy.sympify(2.0)
    res_right_1 = point1 + point2 * num1
    res_left_1 = point1 + num1 * point2
    
    if res_right_1 != res_left_1:
        return ('FAIL', f"Float multiplication mismatch: {res_right_1} != {res_left_1}")

    # Test 2: Symbol
    x = sympy.Symbol('x')
    res_right_2 = point1 + point2 * x
    res_left_2 = point1 + x * point2
    
    if res_right_2 != res_left_2:
        return ('FAIL', f"Symbol multiplication mismatch: {res_right_2} != {res_left_2}")

    # Test 3: Plain Python int
    res_right_3 = point1 + point2 * 3
    res_left_3 = point1 + 3 * point2
    
    if res_right_3 != res_left_3:
        return ('FAIL', f"Int multiplication mismatch: {res_right_3} != {res_left_3}")

    return ('PASS',)

try:
    result = check_issue()
    print(f"RESULT={result!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
