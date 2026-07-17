from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms.widgets import CheckboxInput

attrs = {"data-probe": "value"}
CheckboxInput().get_context("probe", True, attrs)

print(f"RESULT={attrs!r}")
