from django.conf import settings

settings.configure(
    SECRET_KEY="test",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django
django.setup()

from django import forms
from django.db import models
from django.forms.models import construct_instance


class Example(models.Model):
    value = models.IntegerField(default=7, blank=True)

    class Meta:
        app_label = "testapp"


class ExampleForm(forms.ModelForm):
    class Meta:
        model = Example
        fields = ["value"]

    def clean_value(self):
        return 0


form = ExampleForm(data={})
form.is_valid()
instance = construct_instance(form, Example())
print("RESULT=%r" % instance.value)
