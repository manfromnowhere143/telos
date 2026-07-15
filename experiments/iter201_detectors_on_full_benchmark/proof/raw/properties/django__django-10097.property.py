from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="property-test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

try:
    URLValidator()("http://alice:se:cret@example.com")
except ValidationError:
    print("PROP_PASS")
else:
    print("PROP_FAIL")
