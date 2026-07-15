import astropy.units as u


class EqualToNone:
    def __eq__(self, other):
        return other is None


def function(value):
    return "accepted"


function.__annotations__ = {"value": u.V, "return": EqualToNone()}
decorated = u.quantity_input(function)

result = decorated(1.0 * u.V)
print("RESULT=" + repr(result))
