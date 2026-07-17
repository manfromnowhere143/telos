from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="test",
)

import django
django.setup()

from django.db import models
from django.db.models import F, OrderBy
from django.db.models.sql.query import Query


class Target(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "ordering_test"
        ordering = [OrderBy(F("name"))]


class Source(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)

    class Meta:
        app_label = "ordering_test"


compiler = Query(Source).get_compiler(using="default")
result = compiler.find_ordering_name("target", Source._meta)
print("RESULT=" + repr(result))
