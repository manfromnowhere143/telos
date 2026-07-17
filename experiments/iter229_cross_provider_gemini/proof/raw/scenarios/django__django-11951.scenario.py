from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    SECRET_KEY="x",
)

import django

django.setup()

from django.db import connection, models


class Probe(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "probe"


with connection.schema_editor() as editor:
    editor.create_model(Probe)

fields = [Probe._meta.get_field("value")]
maximum = max(connection.ops.bulk_batch_size(fields, []), 1)
objects = [Probe(value=i) for i in range(maximum + 1)]
parameter_counts = []


def capture(execute, sql, params, many, context):
    if sql.lstrip().upper().startswith("INSERT"):
        parameter_counts.append(len(params or ()))
    return execute(sql, params, many, context)


with connection.execute_wrapper(capture):
    Probe.objects.all()._batched_insert(objects, fields, maximum * 2)

print("RESULT=" + repr(tuple(parameter_counts)))
