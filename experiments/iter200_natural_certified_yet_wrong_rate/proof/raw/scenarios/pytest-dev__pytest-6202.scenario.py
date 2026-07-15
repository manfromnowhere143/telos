from _pytest.python import Function


class Probe:
    name = "test.[.["

    def listchain(self):
        return [self]


result = Function.getmodpath(Probe())
print(f"RESULT={result!r}")
