from sympy.combinatorics import Permutation

try:
    result = Permutation([False, False]).array_form
except ValueError as exc:
    result = type(exc).__name__

print("RESULT=" + repr(result))
