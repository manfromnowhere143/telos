import astropy.coordinates as coord

class CustomCoord(coord.SkyCoord):
    def __getattribute__(self, name):
        if name == "special_attr":
            return "intercepted"
        return super().__getattribute__(name)

c = CustomCoord("00h42m30s", "+41d12m00s", frame="icrs")

try:
    result = c.__getattr__("special_attr")
except AttributeError as exc:
    result = str(exc)

print("RESULT=" + repr(result))
