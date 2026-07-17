from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
    )

import django

django.setup()

from django.db import models
from django.db.models import F
from django.db.models.sql.query import Query


class Probe(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "probe"
        db_table = "probe_table"


query = Query(Probe)
result = query.resolve_lookup_value(([F("value")],), set(), True, False)
print("RESULT=" + repr(result))
