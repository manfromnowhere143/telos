from django.db.migrations.serializer import FunctionTypeSerializer


class Holder:
    def method(self):
        pass


print("RESULT=%r" % (FunctionTypeSerializer(Holder.method).serialize(),))
