from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class Parent(models.Model):
    def get_status_display(self):
        return "inherited"

    class Meta:
        app_label = "repro"


class Child(Parent):
    status = models.CharField(max_length=1, choices=[("A", "Alpha")])

    class Meta:
        app_label = "repro"


print("RESULT=%r" % Child(status="A").get_status_display())
