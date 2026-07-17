from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class First(models.Model):
    first_id = models.IntegerField(primary_key=True)

    class Meta:
        app_label = "probe"


class Second(models.Model):
    second_id = models.IntegerField(primary_key=True)

    class Meta:
        app_label = "probe"


class Combined(First, Second):
    class Meta:
        app_label = "probe"


obj = Combined()
obj.pk = 17
print("RESULT=" + repr(obj._get_pk_val(Second._meta)))
