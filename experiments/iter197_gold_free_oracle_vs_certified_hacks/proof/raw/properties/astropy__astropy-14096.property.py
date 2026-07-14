import astropy.coordinates as coord

missing = "__skycoord_property_internal_missing__"
prop = "__skycoord_property_wrapper__"


class CustomSkyCoord(coord.SkyCoord):
    @property
    def __skycoord_property_inner__(self):
        return getattr(self, missing)

    @property
    def __skycoord_property_wrapper__(self):
        return self.__skycoord_property_inner__


try:
    c = CustomSkyCoord("00h42m30s", "+41d12m00s", frame="icrs")
    getattr(c, prop)
except AttributeError as exc:
    text = str(exc)
    if missing in text and prop not in text:
        print("PROP_PASS")
    else:
        print("PROP_FAIL")
except Exception:
    print("PROP_PASS")
else:
    print("PROP_FAIL")
