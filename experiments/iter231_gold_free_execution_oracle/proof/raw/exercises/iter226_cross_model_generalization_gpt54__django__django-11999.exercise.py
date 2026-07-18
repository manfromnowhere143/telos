from django.conf import settings
import django
from django.db import models

try:
    if not settings.configured:
        settings.configure(
            SECRET_KEY="test",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

    class DirectOverride(models.Model):
        value = models.CharField(max_length=1, choices=[("a", "Alpha")])

        def get_value_display(self):
            return "direct override"

        class Meta:
            app_label = "display_fixture"

    class DisplayMixin:
        def get_value_display(self):
            return "inherited override"

    class InheritedOverride(DisplayMixin, models.Model):
        value = models.CharField(max_length=1, choices=[("a", "Alpha")])

        class Meta:
            app_label = "display_fixture"

    print("RESULT=%r" % (
        DirectOverride(value="a").get_value_display(),
        InheritedOverride(value="a").get_value_display(),
    ))
except Exception as exc:
    print("RESULT=%r" % ("ERROR", type(exc).__name__))
