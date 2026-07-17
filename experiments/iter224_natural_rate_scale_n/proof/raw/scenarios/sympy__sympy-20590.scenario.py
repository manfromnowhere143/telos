from sympy.core._print_helpers import Printable

obj = Printable()
print("RESULT=" + repr((Printable.__slots__, hasattr(obj, "__dict__"))))
