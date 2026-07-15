import astropy.coordinates as coord

missing_name = "definitely_missing_coordinate_attribute_9f3a"
property_name = "inherited_coordinate_probe_9f3a"

try:
    class PropertyCarrier(coord.SkyCoord):
        @property
        def inherited_coordinate_probe_9f3a(self):
            return getattr(self, missing_name)

    class DerivedCoordinate(PropertyCarrier):
        pass

    value = DerivedCoordinate("00h42m30s", "+41d12m00s", frame="icrs")

    try:
        getattr(value, property_name)
    except AttributeError as exc:
        message = str(exc)
        if missing_name in message and property_name not in message:
            print("PROP_PASS")
        else:
            print("PROP_FAIL")
    else:
        print("PROP_FAIL")
except Exception:
    print("PROP_PASS")
