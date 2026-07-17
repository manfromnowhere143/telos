from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db import models


class Meta:
    def add_field(self, field, private=False):
        pass


class Parent:
    _meta = Meta()

    def _get_FIELD_display(self, field):
        return "generated"

    def get_state_display(self):
        return "inherited"


class Child(Parent):
    pass


field = models.CharField(max_length=1, choices=[("x", "X")])
field.contribute_to_class(Child, "state")

print("RESULT=" + repr(Child().get_state_display()))
