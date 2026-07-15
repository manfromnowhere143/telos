from django.conf import settings

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.http import HttpResponse

result = HttpResponse().make_bytes(memoryview(b"My Content"))
print(f"RESULT={result!r}")
