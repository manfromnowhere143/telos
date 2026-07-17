from sympy import symbols
from sympy.solvers.diophantine import diophantine

x, y, t = symbols("x y t", integer=True)
solutions = diophantine(x + y - 1, param=t, syms=(y, x), permute=True)
ordered = tuple(sorted(solutions, key=lambda solution: tuple(map(str, solution))))
print("RESULT=" + repr(ordered))
