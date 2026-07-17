from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms.widgets import CheckboxInput


class FalseAttrs(dict):
    def __bool__(self):
        return False


context = CheckboxInput().get_context("flag", True, FalseAttrs(id="preserved"))
print("RESULT=" + repr(context["widget"]["attrs"]))
