from sympy import symbols
from sympy.solvers.diophantine import diophantine

x, y = symbols("x y", integer=True)
solutions = diophantine(x**2 + y**2 - 5, syms=(y, x), permute=True)
result = tuple(sorted(tuple(map(str, solution)) for solution in solutions))
print("RESULT=" + repr(result))
