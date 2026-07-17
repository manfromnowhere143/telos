from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="x",
)

import django

django.setup()

from django.db import DatabaseError, connection, models


class Item(models.Model):
    id = models.IntegerField(primary_key=True, default=7)

    class Meta:
        app_label = "testapp"


with connection.schema_editor() as editor:
    editor.create_model(Item)

try:
    item = Item()
    item.save(force_update=True)
    result = ("saved", Item.objects.count(), item.pk)
except DatabaseError:
    result = ("DatabaseError",)

print("RESULT=" + repr(result))
