from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="test",
)

import django

django.setup()

from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "testapp"


left = Item.objects.values("name")
right = Item.objects.all()
combined = left.union(right)

str(combined.query)

print("RESULT=" + repr(right.query.values_select))
