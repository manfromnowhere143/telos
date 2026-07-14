from django.conf import settings

settings.configure(
    SECRET_KEY="test",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django
django.setup()

from django.db import models
from django.forms.models import model_to_dict


class Sample(models.Model):
    name = models.CharField(max_length=10, default="value")

    class Meta:
        app_label = "testapp"


print("RESULT=" + repr(model_to_dict(Sample(), fields=())))
