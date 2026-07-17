from sympy import Function
from sympy.physics.units import meter
from sympy.physics.units.systems import SI

try:
    result = SI._collect_factor_and_dimension(Function("f")(meter))
except Exception as exc:
    result = (type(exc).__name__, str(exc))

print(f"RESULT={result!r}")
