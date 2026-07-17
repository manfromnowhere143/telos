from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class Item(models.Model):
    code = models.IntegerField()

    class Meta:
        app_label = "detector"
        constraints = [
            models.UniqueConstraint(fields=["code"], name="item_code_unique"),
        ]


Item._meta.constraints[0].fields = ["code"]
print("RESULT=%r" % Item.objects.in_bulk([], field_name="code"))
