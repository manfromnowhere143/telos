# Gold-free metamorphic properties for Point.distance, run inside the pinned SWE-bench container.
# Distance is symmetric and zero to itself - contract identities, no gold needed.
from sympy import Point

p1 = Point(3, 5)
p2 = Point(-2, 7)
checks = {
    "symmetric": p1.distance(p2) == p2.distance(p1),
    "self_zero": p1.distance(p1) == 0,
}
violations = [name for name, ok in checks.items() if not ok]
print("PROP_SOUND" if not violations else "PROP_UNSOUND:" + ",".join(violations))
