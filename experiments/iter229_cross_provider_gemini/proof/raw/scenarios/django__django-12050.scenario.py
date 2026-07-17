from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db import models
from django.db.models import F
from django.db.models.sql.query import Query


class Probe(models.Model):
    field = models.IntegerField()

    class Meta:
        app_label = "probe"


query = Query(Probe)
result = query.resolve_lookup_value(([F("field")],), set(), True, False)
print("RESULT=" + repr(result))
