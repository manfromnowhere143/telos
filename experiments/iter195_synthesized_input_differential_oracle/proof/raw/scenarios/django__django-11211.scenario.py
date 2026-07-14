from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db.models import UUIDField

field = UUIDField()
result = field.get_prep_value("550e8400e29b41d4a716446655440000")
print("RESULT=" + repr(result))
