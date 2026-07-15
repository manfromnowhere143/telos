from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms.widgets import FileInput

widget = FileInput()
value = widget.value_from_datadict({}, {}, "upload")
required = widget.use_required_attribute("existing-file")
print("RESULT=" + repr((value, required)))
