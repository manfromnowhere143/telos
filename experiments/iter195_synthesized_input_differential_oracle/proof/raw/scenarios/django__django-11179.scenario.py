from django.conf import settings

settings.configure(
    SECRET_KEY="test",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import connection, models


class Probe(models.Model):
    token = models.CharField(max_length=20, primary_key=True)

    class Meta:
        app_label = "probe"


with connection.schema_editor() as schema_editor:
    schema_editor.create_model(Probe)

instance = Probe.objects.create(token="present")
instance.delete()

print("RESULT=" + repr(instance.pk))
