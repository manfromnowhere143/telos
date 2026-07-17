from sympy.core.add import Add
from sympy.matrices.expressions.matadd import MatAdd
from sympy.matrices.expressions.matexpr import _postprocessor
from sympy.matrices.expressions.matexpr import MatrixSymbol

A = MatrixSymbol("A", 1, 1)
B = MatrixSymbol("B", 1, 1)
raw = Add._from_args((A, B))
result = _postprocessor(MatAdd)(raw)

print("RESULT=" + repr(result))
