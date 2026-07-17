from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.db import models


class Status(models.TextChoices):
    READY = "ready", "Ready"


print("RESULT=" + repr((Status.values, str(Status.READY))))
