import enum

from django.db.migrations.serializer import EnumSerializer


class Container:
    class Choice(enum.Enum):
        VALUE = 1


result = EnumSerializer(Container.Choice.VALUE).serialize()
print("RESULT=%r" % (result,))
