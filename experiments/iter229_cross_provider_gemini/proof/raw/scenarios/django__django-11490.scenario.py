from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "testapp"


right = Item.objects.all()
combined = Item.objects.values("name").union(right)

str(combined.query)

print("RESULT=" + repr(right.query.values_select))
