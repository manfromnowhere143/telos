from sympy.geometry import Point

class ProbePoint(Point):
    def __getattribute__(self, name):
        if name == "__mul__":
            return lambda factor: "intercepted"
        return super().__getattribute__(name)

result = 3 * ProbePoint(1, 2)
print("RESULT=" + repr(result))
