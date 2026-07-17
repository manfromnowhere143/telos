from django.conf import settings

settings.configure(
    SECRET_KEY="x",
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)

import django

django.setup()

from django.db import connection, models


class BatchProbe(models.Model):
    value = models.IntegerField()

    class Meta:
        app_label = "batch_probe"


with connection.schema_editor() as editor:
    editor.create_model(BatchProbe)

fields = [BatchProbe._meta.get_field("value")]
max_batch_size = max(connection.ops.bulk_batch_size(fields, [BatchProbe(value=0)]), 1)
objects = [BatchProbe(value=i) for i in range(max_batch_size + 1)]
insert_count = [0]


def count_inserts(execute, sql, params, many, context):
    if sql.lstrip().upper().startswith("INSERT"):
        insert_count[0] += 1
    return execute(sql, params, many, context)


with connection.execute_wrapper(count_inserts):
    BatchProbe.objects.all()._batched_insert(
        objects,
        fields,
        batch_size=max_batch_size + 1,
    )

print("RESULT=" + repr(insert_count[0]))
