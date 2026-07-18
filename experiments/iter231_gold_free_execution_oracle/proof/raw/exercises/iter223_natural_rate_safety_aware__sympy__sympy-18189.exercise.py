from sympy import symbols
from sympy.solvers.diophantine import diophantine

try:
    m, n = symbols("m n", integer=True)
    equation = n**4 + m**4 - 2**4 - 3**4
    by_mn = diophantine(equation, syms=(m, n), permute=True)
    by_nm = diophantine(equation, syms=(n, m), permute=True)
    print("RESULT=" + repr((tuple(sorted(by_mn)), tuple(sorted(by_nm)))))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
