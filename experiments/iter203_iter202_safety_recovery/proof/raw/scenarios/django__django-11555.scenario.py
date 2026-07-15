from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)

import django

django.setup()

from django.db import connection, models


class Parent(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "repro"
        ordering = [models.F("value").asc()]


class Child(Parent):
    class Meta:
        app_label = "repro"


compiler = Child.objects.all().query.get_compiler(connection=connection)
result = compiler.find_ordering_name("parent_ptr", Child._meta)
print("RESULT=" + repr(result))
