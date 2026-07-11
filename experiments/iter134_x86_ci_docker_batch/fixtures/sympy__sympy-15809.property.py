# Gold-free metamorphic properties for Min, run inside the pinned SWE-bench container.
# Min is commutative, idempotent, and associative - contract identities that hold for all args,
# no gold needed.
from sympy import symbols, Min

a, b, c = symbols("a b c", real=True)
checks = {
    "commutative": Min(a, b) == Min(b, a),
    "idempotent": Min(a, a) == a,
    "associative": Min(Min(a, b), c) == Min(a, b, c),
}
violations = [name for name, ok in checks.items() if not ok]
print("PROP_SOUND" if not violations else "PROP_UNSOUND:" + ",".join(violations))
