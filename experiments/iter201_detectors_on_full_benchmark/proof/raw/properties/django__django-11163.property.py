from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="prop-test",
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

import django
django.setup()

from django.db import models
from django.forms.models import model_to_dict


class Probe(models.Model):
    value = models.IntegerField(default=1)

    class Meta:
        app_label = "prop_model_to_dict"


instance = Probe(value=7)
result = model_to_dict(instance, fields=())

print("PROP_PASS" if result == {} else "PROP_FAIL")
