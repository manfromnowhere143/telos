from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms.widgets import ClearableFileInput, FILE_INPUT_CONTRADICTION

name = "upload"
result = ClearableFileInput().value_from_datadict(
    {name + "-clear": "on"},
    {name: object()},
    name,
)

print("RESULT=" + repr(result is FILE_INPUT_CONTRADICTION))
