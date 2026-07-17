from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class DisplayMixin:
    def get_status_display(self):
        return "custom"


class Sample(DisplayMixin, models.Model):
    status = models.CharField(max_length=1, choices=[("1", "one")])

    class Meta:
        app_label = "testapp"


print("RESULT=%r" % Sample(status="1").get_status_display())
