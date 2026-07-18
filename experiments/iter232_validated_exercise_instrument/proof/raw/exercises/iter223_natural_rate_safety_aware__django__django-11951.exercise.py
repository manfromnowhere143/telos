try:
    import types
    import django
    from django.apps import apps
    from django.conf import settings
    from django.db import connections, models

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    if not apps.ready:
        django.setup()

    class Item(models.Model):
        name = models.CharField(max_length=20)

        class Meta:
            app_label = "batch_probe"

    queryset = Item.objects.all()
    ops = connections[queryset.db].ops
    ops.bulk_batch_size = lambda fields, objs: 2

    batches = []

    def record_insert(self, objs, fields, **kwargs):
        batches.append(len(objs))
        return []

    queryset._insert = types.MethodType(record_insert, queryset)
    objects = [Item(name=str(i)) for i in range(5)]
    fields = [Item._meta.get_field("name")]

    queryset._batched_insert(objects, fields, 100)
    oversized = tuple(batches)
    batches[:] = []
    queryset._batched_insert(objects, fields, 1)
    undersized = tuple(batches)

    print("RESULT=" + repr((oversized, undersized)))
except Exception as exc:
    print("RESULT=" + repr(("ERROR", type(exc).__name__)))
