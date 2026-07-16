from django.db.migrations.serializer import TypeSerializer


class Probe:
    def __init__(self):
        self.name_was_read = False

    def __getattribute__(self, name):
        if name == "__module__":
            return "probe"
        if name == "__name__":
            object.__setattr__(self, "name_was_read", True)
            return "fallback"
        if name == "__qualname__":
            if object.__getattribute__(self, "name_was_read"):
                return "changed"
            return "original"
        return object.__getattribute__(self, name)


print("RESULT=" + repr(TypeSerializer(Probe()).serialize()))
