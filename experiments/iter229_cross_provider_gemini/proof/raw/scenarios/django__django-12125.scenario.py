from django.db.migrations.serializer import TypeSerializer


class Container:
    class Item:
        pass


Container.Item.__module__ = "builtins"
print("RESULT=" + repr(TypeSerializer(Container.Item).serialize()))
