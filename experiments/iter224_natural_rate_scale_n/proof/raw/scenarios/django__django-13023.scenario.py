from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
    )

import django

django.setup()

from django.core.exceptions import ValidationError
from django.db.models import DecimalField

try:
    DecimalField(max_digits=2, decimal_places=0).to_python((2, (1,), 0))
except ValidationError as exc:
    result = (type(exc).__name__, exc.code)
except Exception as exc:
    result = (type(exc).__name__, str(exc))
else:
    result = "no exception"

print("RESULT=" + repr(result))
