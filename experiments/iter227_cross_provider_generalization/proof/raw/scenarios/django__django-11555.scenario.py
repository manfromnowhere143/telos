from django.conf import settings

settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)

import django

django.setup()

from django.db import connection, models


class Related(models.Model):
    label = models.CharField(max_length=20)

    class Meta:
        app_label = "ordering_probe"
        ordering = [models.F("label").asc()]


class Parent(models.Model):
    rel = models.ForeignKey(Related, on_delete=models.CASCADE)

    class Meta:
        app_label = "ordering_probe"


compiler = Parent.objects.all().query.get_compiler(using="default")
result = compiler.find_ordering_name("-rel", Parent._meta)
print("RESULT=" + repr([(item.descending, is_reference) for item, is_reference in result]))
