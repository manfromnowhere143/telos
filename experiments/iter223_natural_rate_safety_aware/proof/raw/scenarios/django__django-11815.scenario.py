from enum import Enum

from django.db.migrations.serializer import EnumSerializer

QuotedNameEnum = Enum("QuotedNameEnum", {"O'REILLY": "value"})
serialized, _ = EnumSerializer(QuotedNameEnum["O'REILLY"]).serialize()

print("RESULT=%r" % serialized)
