from types import SimpleNamespace

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

import django

django.setup()

from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.db import models
from django.http import QueryDict


class Probe(models.Model):
    class Meta:
        app_label = "probe"


request = SimpleNamespace(
    POST=QueryDict("items%5B0%5D-0-id=literal&items0-1-id=decoy")
)
admin = ModelAdmin(Probe, AdminSite())
result = admin._get_edited_object_pks(request, "items[0]")

print("RESULT={!r}".format(result))
