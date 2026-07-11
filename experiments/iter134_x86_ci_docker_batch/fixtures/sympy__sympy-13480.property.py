# Gold-free metamorphic property for coth, run inside the pinned SWE-bench container.
# coth is odd and the reciprocal of tanh - contract properties that hold for all x, no gold needed.
from sympy import symbols, coth, tanh, simplify

x = symbols("x")
checks = {
    "coth_odd": coth(-x) + coth(x),
    "coth_reciprocal": coth(x) * tanh(x) - 1,
}
violations = [name for name, expr in checks.items() if simplify(expr) != 0]
print("PROP_SOUND" if not violations else "PROP_UNSOUND:" + ",".join(violations))
