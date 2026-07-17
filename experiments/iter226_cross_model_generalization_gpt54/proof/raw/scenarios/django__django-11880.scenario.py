import copy

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms.fields import Field

marker = []
field = Field(error_messages={"required": marker})
cloned = copy.deepcopy(field)

print("RESULT=" + repr(cloned.error_messages["required"] is marker))
