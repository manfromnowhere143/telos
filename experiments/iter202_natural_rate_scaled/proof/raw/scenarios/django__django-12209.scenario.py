from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    SECRET_KEY="test",
)

import django

django.setup()

from uuid import UUID
from django.db import connection, models


class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID)
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "testapp"


with connection.schema_editor() as editor:
    editor.create_model(Sample)

pk = UUID("12345678-1234-5678-1234-567812345678")
Sample.objects.create(id=pk, name="old")

instance = Sample(id=pk, name="new")
instance.save_base(raw=True, using="default")

print("RESULT=" + repr(Sample.objects.get(pk=pk).name))
