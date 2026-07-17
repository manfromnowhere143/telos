from django.db.migrations.serializer import TypeSerializer


class Outer:
    class Inner:
        pass


print("RESULT=" + repr(TypeSerializer(Outer.Inner).serialize()))
