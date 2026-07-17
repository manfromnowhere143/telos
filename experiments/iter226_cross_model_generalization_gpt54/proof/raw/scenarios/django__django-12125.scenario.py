from django.db.migrations.serializer import serializer_factory


def make_value():
    class NestedType:
        pass

    NestedType.__module__ = "builtins"
    return NestedType


print("RESULT=%r" % (serializer_factory(make_value()).serialize(),))
