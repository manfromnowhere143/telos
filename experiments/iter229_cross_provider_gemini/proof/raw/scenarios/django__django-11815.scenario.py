import datetime
from enum import Enum

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db.migrations.serializer import EnumSerializer


class Probe(Enum):
    MEMBER = 1


Probe.MEMBER._name_ = datetime.date
serialized, imports = EnumSerializer(Probe.MEMBER).serialize()
print("RESULT=%r" % ((serialized, tuple(sorted(imports))),))
