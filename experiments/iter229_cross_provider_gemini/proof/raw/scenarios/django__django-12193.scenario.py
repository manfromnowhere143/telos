from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
    )

import django
django.setup()

from django.forms.widgets import CheckboxInput

context = CheckboxInput().get_context("field", True, {})
print("RESULT=" + repr(context["widget"]["attrs"]))
