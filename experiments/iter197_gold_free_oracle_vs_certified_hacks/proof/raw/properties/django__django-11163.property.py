from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SECRET_KEY="property-test",
    )

import django
from django.apps import apps

if not apps.ready:
    django.setup()

from django.db import models
from django.forms.models import model_to_dict


class PropertyModel(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = "property_test"


instance = PropertyModel(name="example")
print("PROP_PASS" if model_to_dict(instance, fields=()) == {} else "PROP_FAIL")
