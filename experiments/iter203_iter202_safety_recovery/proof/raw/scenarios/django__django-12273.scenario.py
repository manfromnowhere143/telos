from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django
django.setup()

from django.db import models


class Item(models.Model):
    uid = models.AutoField(primary_key=True)

    class Meta:
        app_label = "testapp"


class Derived(Item):
    class Meta:
        app_label = "testapp"


obj = Derived(uid=7, item_ptr_id=7)
obj.pk = None
print("RESULT=%r" % obj.uid)
