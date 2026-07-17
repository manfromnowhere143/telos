from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="x",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
from django.apps import apps

if not apps.ready:
    django.setup()

from django.db import models


class Probe(models.Model):
    name = models.CharField(max_length=16)

    class Meta:
        app_label = "probe"


queryset = Probe.objects.values("name").union(Probe.objects.all())
compiler = queryset.query.get_compiler(using="default")
compiler.get_combinator_sql("union", False)

print("RESULT=" + repr(queryset.query.combined_queries[1].values_select))
