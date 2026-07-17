import copy

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[],
    )

import django

django.setup()

from django.forms.fields import Field


class Marker:
    def __deepcopy__(self, memo):
        return "copied"


marker = Marker()
field = Field(error_messages={"custom": marker})
cloned = copy.deepcopy(field)

print("RESULT=" + repr(cloned.error_messages["custom"] is marker))
