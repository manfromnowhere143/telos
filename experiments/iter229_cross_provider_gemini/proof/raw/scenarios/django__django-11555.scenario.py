from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import connection, models
from django.db.models import F, OrderBy
from django.db.models.sql.query import Query


class Parent(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "probe"
        ordering = [OrderBy(F("value"))]


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class Meta:
        app_label = "probe"


compiler = Query(Child).get_compiler(connection=connection)
result = compiler.find_ordering_name("-parent", Child._meta)
observable = [
    (item.expression.name, item.descending, item.nulls_first, item.nulls_last, flag)
    for item, flag in result
]
print("RESULT=" + repr(observable))
