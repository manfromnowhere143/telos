from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import models


class ParentA(models.Model):
    a_key = models.IntegerField(primary_key=True)

    class Meta:
        app_label = "probe"


class ParentB(models.Model):
    b_key = models.IntegerField(primary_key=True)

    class Meta:
        app_label = "probe"


class Child(ParentA, ParentB):
    class Meta:
        app_label = "probe"


obj = Child()
obj.pk = 41
result = (
    obj._get_pk_val(),
    obj.a_ptr_id,
    obj.b_key,
    obj.b_ptr_id,
)
print("RESULT=" + repr(result))
