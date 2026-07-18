try:
    from django.conf import settings
    import django
    from django.db import models

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            SECRET_KEY="test",
        )
    if not hasattr(django, "setup"):
        raise RuntimeError("django.setup unavailable")
    django.setup()

    class Item(models.Model):
        uid = models.AutoField(primary_key=True, editable=False)

        class Meta:
            app_label = "pk_reset_test"

    class Derived(Item):
        class Meta:
            app_label = "pk_reset_test"

    obj = Derived(uid=7)
    obj.pk = None
    result = (obj.pk, obj.uid)
    print(f"RESULT={result!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
