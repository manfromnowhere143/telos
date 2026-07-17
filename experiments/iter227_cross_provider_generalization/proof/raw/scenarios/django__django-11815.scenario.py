import enum

from django.db.migrations.serializer import EnumSerializer


class Probe(enum.Enum):
    MEMBER = object()


try:
    result = EnumSerializer(Probe.MEMBER).serialize()
except Exception as exc:
    result = ("ERROR", type(exc).__name__)

print("RESULT=%r" % (result,))
