import copy

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.forms import CharField

message = []
field = CharField(error_messages={"required": message})
cloned = copy.deepcopy(field)

print("RESULT=%r" % (
    field.error_messages is cloned.error_messages,
    field.error_messages["required"] is cloned.error_messages["required"],
))
