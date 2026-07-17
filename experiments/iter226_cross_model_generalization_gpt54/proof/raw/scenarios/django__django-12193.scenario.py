from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_I18N=False,
    )

import django

django.setup()

from django.forms.widgets import CheckboxInput


class ProbeAttrs(dict):
    def copy(self):
        return {"probe": "copy"}


context = CheckboxInput().get_context("field", True, ProbeAttrs({"probe": "original"}))
print("RESULT=" + repr(context["widget"]["attrs"]))
