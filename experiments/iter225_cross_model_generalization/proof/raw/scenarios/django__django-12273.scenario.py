from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django

django.setup()

from django.db import models


class ParentA(models.Model):
    a_id = models.AutoField(primary_key=True)

    class Meta:
        app_label = "pk_probe"


class ParentB(models.Model):
    b_id = models.AutoField(primary_key=True)

    class Meta:
        app_label = "pk_probe"


class Child(ParentA, ParentB):
    class Meta:
        app_label = "pk_probe"


obj = Child()
obj.b_id = None
obj.pk = 37
print("RESULT=" + repr((obj._get_pk_val(), obj.b_id)))
