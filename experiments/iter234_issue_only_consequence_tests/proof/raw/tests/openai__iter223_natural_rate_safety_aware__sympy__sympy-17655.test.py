import sympy
from sympy import geometry as ge

try:
    point = ge.Point(3, -1)
    offset = ge.Point(-2, 4)
    scale = sympy.sympify(2.5)

    left_product = scale * point
    right_product = point * scale

    assert isinstance(left_product, ge.Point)
    assert left_product == right_product
    assert offset + left_product == offset + right_product
    assert offset + left_product == ge.Point(sympy.sympify(5.5), sympy.sympify(1.5))

    print(f"RESULT={('PASS',)!r}")
except AssertionError:
    print(f"RESULT={('FAIL', 'scalar point mismatch')!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
