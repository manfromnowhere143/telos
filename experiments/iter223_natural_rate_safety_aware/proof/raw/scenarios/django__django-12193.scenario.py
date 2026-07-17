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

results = iter((True, False))
widget = CheckboxInput(check_test=lambda value: next(results, False))
context = widget.get_context("field", "value", {})

print("RESULT=" + repr(context["widget"]["attrs"]))
