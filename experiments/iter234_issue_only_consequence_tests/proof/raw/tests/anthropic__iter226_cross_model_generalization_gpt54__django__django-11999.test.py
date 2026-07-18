try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "testapp"],
            DATABASES={},
        )
    import django as dj
    dj.setup()
    from django.db import models

    class FooBar(models.Model):
        foo_bar = models.CharField(max_length=10, choices=[(1, "foo"), (2, "bar")])

        class Meta:
            app_label = "testapp"

        def get_foo_bar_display(self):
            return "something"

    class Baz(models.Model):
        val = models.IntegerField(choices=[(1, "foo"), (2, "bar")])

        class Meta:
            app_label = "testapp"

    obj = FooBar(foo_bar=1)
    result = obj.get_foo_bar_display()
    assert result == "something", f"override ignored: {result!r}"

    # Ensure non-overridden still works normally
    b = Baz(val=2)
    assert b.get_val_display() == "bar", f"default broken: {b.get_val_display()!r}"

    print(f"RESULT={('PASS',)!r}")
except Exception as exc:
    print(f"RESULT={('ERROR', type(exc).__name__)!r}")
