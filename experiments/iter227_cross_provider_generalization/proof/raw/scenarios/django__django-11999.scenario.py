from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
    )

import django

django.setup()

from django.db import models


class NoColumnField(models.Field):
    def get_attname_column(self):
        return self.get_attname(), None


class Probe(models.Model):
    class Meta:
        app_label = "probe_app"


field = NoColumnField(choices=((1, "one"),))
field.contribute_to_class(Probe, "probe_value")

print(
    "RESULT=%r"
    % (
        hasattr(Probe, "probe_value"),
        hasattr(Probe, "get_probe_value_display"),
    )
)
