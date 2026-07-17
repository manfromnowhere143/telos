from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.contrib.admin.utils import display_for_field
from django.db import models

result = display_for_field({1}, models.JSONField(), "-")
print(f"RESULT={result!r}")
