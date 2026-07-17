import sympy.core.numbers as numbers
from sympy.core.basic import Basic
from sympy import Float

class Trigger(Basic):
    @property
    def is_NumberSymbol(self):
        numbers.Boolean = Trigger
        return False

    def __bool__(self):
        return False

result = Float(0).__eq__(Trigger())
print(f"RESULT={result!r}")
