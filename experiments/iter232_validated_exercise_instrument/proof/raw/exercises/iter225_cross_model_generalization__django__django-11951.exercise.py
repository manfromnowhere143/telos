try:
    from django.conf import settings
    from django.apps import apps
    import django

    if not settings.configured:
        settings.configure(
            SECRET_KEY="probe",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    if not apps.ready:
        django.setup()

    from django.db import connection, models

    class Probe(models.Model):
        value = models.IntegerField()

        class Meta:
            app_label = "batch_probe"
            db_table = "batch_probe_table"

    with connection.schema_editor() as editor:
        editor.create_model(Probe)

    inserts = []

    def record(execute, sql, params, many, context):
        if sql.lstrip().upper().startswith("INSERT"):
            inserts.append(len(params) if params is not None else None)
        return execute(sql, params, many, context)

    original_bulk_batch_size = connection.ops.bulk_batch_size
    connection.ops.bulk_batch_size = lambda fields, objs: 2
    try:
        with connection.execute_wrapper(record):
            Probe.objects.bulk_create(
                [Probe(value=i) for i in range(5)],
                batch_size=100,
            )
    finally:
        connection.ops.bulk_batch_size = original_bulk_batch_size

    print("RESULT=" + repr((tuple(inserts), Probe.objects.count())))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
