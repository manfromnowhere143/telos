from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db import models


class OrderingLookupModel(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "ordering_lookup_test"
        ordering = ["value__isnull"]


errors = OrderingLookupModel._check_ordering()
print("RESULT=" + repr([(error.id, error.msg) for error in errors]))
