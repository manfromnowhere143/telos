from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

try:
    URLValidator()("http://foo/bar@example.com")
    result = "accepted"
except ValidationError:
    result = "rejected"

print("RESULT=" + repr(result))
