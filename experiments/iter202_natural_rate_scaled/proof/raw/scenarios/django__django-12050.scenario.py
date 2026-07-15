from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.db.models.sql.query import Query

result = Query(None).resolve_lookup_value(["sentinel"], None, True, False)
print("RESULT=" + repr(result))
