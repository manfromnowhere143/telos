from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db.models import Field


class Meta:
    def add_field(self, field, private=False):
        pass


class Base:
    _meta = Meta()

    def get_status_display(self):
        return "inherited"

    def _get_FIELD_display(self, field):
        return "generated:" + field.name


class Child(Base):
    pass


field = Field(choices=(("a", "A"),))
field.contribute_to_class(Child, "status")

print("RESULT=" + repr(Child().get_status_display()))
