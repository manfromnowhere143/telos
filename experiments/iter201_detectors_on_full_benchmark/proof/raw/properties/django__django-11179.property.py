import sys

result = "PROP_PASS"

try:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="property-test",
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
    from django.db.models.deletion import Collector

    class FastDeleteCustomPK(models.Model):
        code = models.CharField(max_length=40, primary_key=True)

        class Meta:
            app_label = "delete_property"
            db_table = "delete_property_fast_custom_pk"

    with connection.schema_editor() as editor:
        editor.create_model(FastDeleteCustomPK)

    obj = FastDeleteCustomPK.objects.create(code="non_numeric_primary_key")
    collector = Collector(using="default")

    if collector.can_fast_delete(obj):
        obj.delete()
        if obj.pk is not None or FastDeleteCustomPK.objects.filter(
            code="non_numeric_primary_key"
        ).exists():
            result = "PROP_FAIL"
except Exception:
    pass

print(result)
