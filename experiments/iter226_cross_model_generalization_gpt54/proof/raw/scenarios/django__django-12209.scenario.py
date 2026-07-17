from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="x",
)

import django

django.setup()

from django.db import connection, models


def zero():
    return 0


class RawDefaultPK(models.Model):
    id = models.IntegerField(primary_key=True, default=zero)
    value = models.CharField(max_length=20)

    class Meta:
        app_label = "repro"


with connection.schema_editor() as editor:
    editor.create_model(RawDefaultPK)

RawDefaultPK.objects.create(id=0, value="old")

try:
    obj = RawDefaultPK(id=0, value="new")
    obj.save_base(raw=True, using="default")
    result = RawDefaultPK.objects.get(pk=0).value
except Exception as exc:
    result = type(exc).__name__

print("RESULT=" + repr(result))
