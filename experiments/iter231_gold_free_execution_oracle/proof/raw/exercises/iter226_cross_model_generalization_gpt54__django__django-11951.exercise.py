import uuid

try:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="bulk-create-probe",
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )

    import django
    from django.apps import apps
    from django.db import connection, models

    if not apps.ready:
        django.setup()

    table_name = "bulk_create_probe_" + uuid.uuid4().hex

    class Probe(models.Model):
        value = models.IntegerField()

        class Meta:
            app_label = "bulk_create_probe"
            db_table = table_name

    created = False
    original_bulk_batch_size = connection.ops.bulk_batch_size

    try:
        with connection.schema_editor() as editor:
            editor.create_model(Probe)
        created = True

        connection.ops.bulk_batch_size = lambda fields, objs: 2

        def run_case(batch_size):
            batches = []

            def recorder(execute, sql, params, many, context):
                if sql.lstrip().upper().startswith("INSERT"):
                    batches.append(len(params or ()))
                return execute(sql, params, many, context)

            with connection.execute_wrapper(recorder):
                Probe.objects.bulk_create(
                    [Probe(value=i) for i in range(5)],
                    batch_size=batch_size,
                )
            return tuple(batches)

        result = (
            ("large_explicit", run_case(99)),
            ("small_explicit", run_case(1)),
            ("none", run_case(None)),
            ("zero", run_case(0)),
            ("rows", Probe.objects.count()),
        )
    finally:
        connection.ops.bulk_batch_size = original_bulk_batch_size
        if created:
            with connection.schema_editor() as editor:
                editor.delete_model(Probe)

    print("RESULT=" + repr(result))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
